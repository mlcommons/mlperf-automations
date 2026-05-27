"""Parse vLLM startup logs to extract serving configuration.

Reads a vLLM server log file and extracts parallelism and batch-size settings
from the LLMEngine initialisation line. Writes a JSON file with the results.

Usage:
    parse.py --log-path <path> --out-file <path>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

# Patterns cover two vLLM log formats:
#   <=0.19.x: non-default args: {'tensor_parallel_size': 2, 'max_num_seqs': 32, ...}
#   >=0.20.x: Initializing a V1 LLM engine ... with config: ..., tensor_parallel_size=2, ...
# [=:] matches either the '=' (new) or ':' (old dict-repr) separator.
_PATTERNS: list[tuple[str, str]] = [
    ("tensor_parallel",   r"tensor_parallel_size\s*[=:]\s*'?(\d+)"),
    ("pipeline_parallel", r"pipeline_parallel_size\s*[=:]\s*'?(\d+)"),
    ("expert_parallel",   r"expert_parallel_size\s*[=:]\s*'?(\d+)"),
    ("batch",             r"max_num_seqs\s*[=:]\s*'?(\d+)"),
]

# Read at most this many bytes from the start of the log file.
# vLLM prints its engine config (tensor_parallel_size, etc.) near the top during startup.
_HEAD_BYTES = 2 * 1024 * 1024  # 2 MiB


def _read_log_head(path: str) -> str:
    with open(path, "rb") as fh:
        data = fh.read(_HEAD_BYTES)
    return data.decode("utf-8", errors="replace")


def _detect_framework(text: str) -> str:
    """Identify serving framework and version from log text."""
    version_m = re.search(r"version\s+(\d+\.\d+\.\d+)", text)
    version = version_m.group(1) if version_m else ""
    if re.search(r"(?i)vllm", text):
        return f"vLLM {version}".strip() if version else "vLLM"
    if re.search(r"(?i)sglang", text):
        return f"SGLang {version}".strip() if version else "SGLang"
    return ""


def parse_vllm_log(log_path: str) -> dict:
    result: dict = {k: None for k, _ in _PATTERNS}
    result["framework"] = ""

    if not log_path:
        print("No log path provided; writing all-null output.", flush=True)
        return result
    if not os.path.exists(log_path):
        print(f"Log file not found: {log_path!r}; writing all-null output.", flush=True)
        return result

    text = _read_log_head(log_path)

    for field, pattern in _PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            # Take the last match — handles duplicate keys in the dict repr (last value wins).
            result[field] = int(matches[-1])

    result["framework"] = _detect_framework(text)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-path", default="", help="Path to the vLLM server log file")
    parser.add_argument("--out-file", required=True, help="Path to write the output JSON")
    args = parser.parse_args()

    config = parse_vllm_log(args.log_path)

    os.makedirs(os.path.dirname(os.path.abspath(args.out_file)), exist_ok=True)
    with open(args.out_file, "w") as fh:
        json.dump(config, fh, indent=2)

    found = {k: v for k, v in config.items() if v is not None}
    if found:
        print(f"Serving config extracted: {found}", flush=True)
    else:
        print("No serving config values found in log; writing all-null output.", flush=True)


if __name__ == "__main__":
    main()
