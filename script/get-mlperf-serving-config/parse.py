"""Parse serving-framework startup logs to extract serving configuration.

Reads a vLLM, SGLang, or TRT-LLM server log file and extracts parallelism and
batch-size settings. Writes a JSON file with the results.

Usage:
    parse.py --log-path <path> --out-file <path> [--serving-framework auto|vllm|sglang|trtllm]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# vLLM patterns cover two log formats:
#   <=0.19.x: non-default args: {'tensor_parallel_size': 2, 'max_num_seqs': 32, ...}
#   >=0.20.x: Initializing a V1 LLM engine ... with config: ..., tensor_parallel_size=2, ...
# [=:] matches either the '=' (new) or ':' (old dict-repr) separator.
_VLLM_PATTERNS: list[tuple[str, str]] = [
    ("tensor_parallel", r"tensor_parallel_size\s*[=:]\s*'?(\d+)"),
    ("pipeline_parallel", r"pipeline_parallel_size\s*[=:]\s*'?(\d+)"),
    ("expert_parallel", r"expert_parallel_size\s*[=:]\s*'?(\d+)"),
    ("data_parallel", r"data_parallel_size\s*[=:]\s*'?(\d+)"),
    ("batch", r"max_num_seqs\s*[=:]\s*'?(\d+)"),
    ("disaggregated", r"enable_disagg_prefill\s*[=:]\s*'?True"),
]

# SGLang patterns match the server_args=ServerArgs(...) startup line.
# max_running_requests=None does not match \d+, so batch stays null when
# unlimited.
_SGLANG_PATTERNS: list[tuple[str, str]] = [
    ("tensor_parallel", r"tp_size=(\d+)"),
    ("pipeline_parallel", r"pp_size=(\d+)"),
    ("expert_parallel", r"ep_size=(\d+)"),
    ("data_parallel", r"dp_size=(\d+)"),
    ("batch", r"max_running_requests=(\d+)"),
    ("disaggregated", r"disaggregation_mode='(?!null)[^']+"),
]

# TRT-LLM patterns.
# 1.2.x (latest stable): LLM Args dump contains tensor/pipeline_parallel_size
#   and orchestrator_type
# 1.0.x:
#   "[TRT-LLM] [I] max_seq_len=..., max_num_tokens=..., max_batch_size=..." line
# is present, so tensor/pipeline_parallel and disaggregated return null on
# 1.0.x.
_TRTLLM_PATTERNS: list[tuple[str, str]] = [
    ("tensor_parallel", r"tensor_parallel_size=(\d+)"),
    ("pipeline_parallel", r"pipeline_parallel_size=(\d+)"),
    ("batch", r"max_batch_size=(\d+)"),
    ("max_num_tokens", r"max_num_tokens=(\d+)"),
    # orchestrator_type=None → standard; non-None → disaggregated (1.2.x+
    # only).
    ("disaggregated", r"orchestrator_type=(?!None)\S+"),
]


def _choose_patterns(
        text: str, serving_framework: str) -> list[tuple[str, str]]:
    if serving_framework == "vllm":
        return _VLLM_PATTERNS
    if serving_framework == "sglang":
        return _SGLANG_PATTERNS
    if serving_framework == "trtllm":
        return _TRTLLM_PATTERNS
    # auto: detect from log content
    if re.search(r"\[TRT-LLM\]|\[TensorRT-LLM\]", text):
        return _TRTLLM_PATTERNS
    if re.search(r"(?i)sglang", text):
        return _SGLANG_PATTERNS
    return _VLLM_PATTERNS


# Read at most this many bytes from the start of the log file.
# Serving frameworks print their config near the top during startup.
_HEAD_BYTES = 2 * 1024 * 1024  # 2 MiB


def _read_log_head(path: str) -> str:
    with open(path, "rb") as fh:
        data = fh.read(_HEAD_BYTES)
    return data.decode("utf-8", errors="replace")


def _detect_framework(text: str) -> str:
    """Identify serving framework and version from log text."""
    # TRT-LLM: version banner is "[TensorRT-LLM] TensorRT LLM version: X.Y.Z"
    m = re.search(
        r"\[TensorRT-LLM\]\s+TensorRT LLM version:\s*(\d+\.\d+\.\d+)", text)
    if m:
        return f"TRT-LLM {m.group(1)}"
    if re.search(r"\[TRT-LLM\]|\[TensorRT-LLM\]", text):
        return "TRT-LLM"

    # vLLM / SGLang: version number appears near the framework keyword
    version_m = re.search(r"version\s+(\d+\.\d+\.\d+)", text)
    version = version_m.group(1) if version_m else ""
    if re.search(r"(?i)vllm", text):
        return f"vLLM {version}".strip() if version else "vLLM"
    if re.search(r"(?i)sglang", text):
        return f"SGLang {version}".strip() if version else "SGLang"
    return ""


def _build_config_summary(result: dict) -> str:
    """Build a human-readable summary string from non-null, non-zero parallel fields."""
    parts = []
    if result.get("disaggregated"):
        parts.append("Disaggregated")
    for key, label in (("expert_parallel", "EP"), ("pipeline_parallel", "PP"),
                       ("tensor_parallel", "TP"), ("data_parallel", "DP")):
        v = result.get(key)
        if v:
            parts.append(f"{label} {v}")
    notes = result.get("config_summary_notes") or ""
    if notes:
        parts.append(notes)
    return ", ".join(parts)


def parse_serving_log(log_path: str, serving_framework: str = "auto") -> dict:
    # Initialise with vLLM keys as a safe default; overwritten once text is
    # available.
    result: dict = {k: (0 if k == "disaggregated" else None)
                    for k, _ in _VLLM_PATTERNS}
    result.update({"framework": "",
                   "config_summary_notes": "",
                   "config_summary": ""})

    if not log_path:
        print("No log path provided; writing all-null output.", flush=True)
        return result
    if not os.path.exists(log_path):
        print(
            f"Log file not found: {log_path!r}; writing all-null output.",
            flush=True)
        return result

    text = _read_log_head(log_path)
    patterns = _choose_patterns(text, serving_framework)

    result = {k: (0 if k == "disaggregated" else None) for k, _ in patterns}
    result.update({"framework": "",
                   "config_summary_notes": "",
                   "config_summary": ""})

    for field, pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            val = matches[-1]
            # Numeric fields have a (\d+) capture group; disaggregated has none
            # so findall returns the full match string — treat any match as 1.
            result[field] = int(val) if val.isdigit() else 1

    result["framework"] = _detect_framework(text)
    result["config_summary"] = _build_config_summary(result)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--log-path",
        default="",
        help="Path to the server log file")
    parser.add_argument(
        "--out-file",
        required=True,
        help="Path to write the output JSON")
    parser.add_argument(
        "--serving-framework",
        default="auto",
        choices=["auto", "vllm", "sglang", "trtllm"],
        help="Serving framework for log pattern selection (default: auto)")
    args = parser.parse_args()

    config = parse_serving_log(args.log_path, args.serving_framework)

    os.makedirs(os.path.dirname(os.path.abspath(args.out_file)), exist_ok=True)
    with open(args.out_file, "w") as fh:
        json.dump(config, fh, indent=2)

    found = {k: v for k, v in config.items() if v is not None}
    if found:
        print(f"Serving config extracted: {found}", flush=True)
    else:
        print(
            "No serving config values found in log; writing all-null output.",
            flush=True)


if __name__ == "__main__":
    main()
