# SPDX-License-Identifier: Apache-2.0
"""Orchestrate a multi-point MLPerf Endpoints submission run.

Reads its configuration from MLC_MLPERF_ENDPOINTS_SUB_* environment variables
(populated by customize.py), then:

  1. Selects concurrency points covering the four §5 regions for the declared
     Maximum Supported Concurrency M (read from system_desc.json).
  2. Runs the inference-endpoint benchmark (load_pattern=concurrency, streaming
     on) once per point, producing a run folder, and copies system_desc.json in.
  3. Registers each run folder with `endpoints-submission-cli runs create`
     (or `--dry-run` when MLC_MLPERF_ENDPOINTS_SUB_RUNS_DRY_RUN=yes).
  4. Assembles + checks the submission with
     `endpoints-submission-cli submissions create ... --dry-run` (never submits).

The benchmark venv python, the submission-cli executable, and the cli venv
python (used only for the §5.5 region math) are passed in via env. Region/
duration math is delegated to the installed submission_checker library so the
official algorithm is the single source of truth.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path

# --- region / duration helpers (delegated to the submission_checker library) ---

_REGION_SNIPPET = (
    "import json,sys;"
    "from submission_checker.models import compute_regions as cr;"
    "from submission_checker.models.regions import MIN_DURATION_MS as md;"
    "r=cr(max(int(sys.argv[1]),33));"
    "print(json.dumps({"
    "'regions':{"
    "'low_latency':[r.low_latency.start,r.low_latency.end],"
    "'low_throughput':[r.low_throughput.start,r.low_throughput.end],"
    "'med_throughput':[r.med_throughput.start,r.med_throughput.end],"
    "'high_throughput':[r.high_throughput.start,r.high_throughput.end]},"
    "'min_duration_ms':md}))"
)

REGION_ORDER = ["low_latency", "low_throughput", "med_throughput", "high_throughput"]


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _log(msg: str) -> None:
    print(msg, flush=True)


def get_region_info(cli_python: str, m: int) -> dict:
    out = subprocess.check_output([cli_python, "-c", _REGION_SNIPPET, str(m)], text=True)
    return json.loads(out)


def select_points(regions: dict, num_points: int, explicit: list[int] | None) -> list[int]:
    """Return a sorted, de-duplicated concurrency list covering all four regions."""
    if explicit:
        return sorted(set(explicit))

    points: list[int] = []
    # One representative (region midpoint) per region first — guarantees coverage.
    for name in REGION_ORDER:
        start, end = regions[name]
        points.append(max(start, min((start + end) // 2, end)))

    # Spread the remaining points evenly inside each region, round-robin.
    target = max(num_points, len(REGION_ORDER))
    region_idx = 0
    guard = 0
    while len(set(points)) < target and guard < 100_000:
        guard += 1
        name = REGION_ORDER[region_idx % len(REGION_ORDER)]
        region_idx += 1
        start, end = regions[name]
        span = end - start + 1
        if span <= 0:
            continue
        # walk candidate concurrencies in this region until a new one is found
        for offset in range(span):
            cand = start + offset
            if cand not in points:
                points.append(cand)
                break
    return sorted(set(points))[:max(num_points, len(REGION_ORDER))]


def _accuracy_dataset_arg(prompt_col: str) -> str | None:
    """Build the `acc:...` dataset argument, or None if accuracy is not configured."""
    acc_path = _env("MLC_MLPERF_ENDPOINTS_SUB_ACC_DATASET_PATH")
    if not acc_path:
        return None
    suffixes = []
    n = _env("MLC_MLPERF_ENDPOINTS_SUB_ACC_NUM_SAMPLES")
    if n:
        suffixes.append(f"samples={n}")
    acc_prompt = _env("MLC_MLPERF_ENDPOINTS_SUB_ACC_PROMPT_COLUMN") or prompt_col
    if acc_prompt:
        suffixes.append(f"parser.prompt={acc_prompt}")
    eval_method = _env("MLC_MLPERF_ENDPOINTS_SUB_EVAL_METHOD")
    if eval_method:
        suffixes.append(f"accuracy_config.eval_method={eval_method}")
    ground_truth = _env("MLC_MLPERF_ENDPOINTS_SUB_GROUND_TRUTH")
    if ground_truth:
        suffixes.append(f"accuracy_config.ground_truth={ground_truth}")
    extractor = _env("MLC_MLPERF_ENDPOINTS_SUB_EXTRACTOR")
    if extractor:
        suffixes.append(f"accuracy_config.extractor={extractor}")
    arg = "acc:" + acc_path
    if suffixes:
        arg += "," + ",".join(suffixes)
    return arg


def build_benchmark_cmd(ep_python: str, concurrency: int, duration: str,
                        report_dir: Path, with_accuracy: bool = False) -> list[str]:
    url = _env("MLC_MLPERF_ENDPOINTS_SUB_URL")
    model = _env("MLC_MLPERF_ENDPOINTS_SUB_MODEL")
    dataset = _env("MLC_MLPERF_ENDPOINTS_SUB_DATASET_PATH")
    prompt_col = _env("MLC_MLPERF_ENDPOINTS_SUB_PROMPT_COLUMN")
    num_samples = _env("MLC_MLPERF_ENDPOINTS_SUB_NUM_SAMPLES")
    workers = _env("MLC_MLPERF_ENDPOINTS_SUB_NUM_WORKERS")
    tokenizer = _env("MLC_MLPERF_ENDPOINTS_SUB_TOKENIZER")

    perf_arg = "perf:" + dataset
    suffixes = []
    if num_samples:
        suffixes.append(f"samples={num_samples}")
    if prompt_col:
        suffixes.append(f"parser.prompt={prompt_col}")
    if suffixes:
        perf_arg += "," + ",".join(suffixes)

    cmd = [ep_python, "-m", "inference_endpoint.main", "benchmark", "online",
           "--endpoints", url, "--model", model, "--dataset", perf_arg,
           "--load-pattern", "concurrency", "--concurrency", str(concurrency),
           "--duration", duration, "--streaming", "on",
           "--report-dir", str(report_dir)]

    if with_accuracy:
        acc_arg = _accuracy_dataset_arg(prompt_col)
        if acc_arg:
            cmd += ["--dataset", acc_arg, "--mode", "both"]

    if workers:
        cmd += ["--workers", workers]
    max_conns = _env("MLC_MLPERF_ENDPOINTS_SUB_MAX_CONNECTIONS")
    if max_conns:
        cmd += ["--max-connections", max_conns]
    if tokenizer:
        cmd += ["--tokenizer", tokenizer]
    if _env("MLC_MLPERF_ENDPOINTS_SUB_NO_CPU_AFFINITY", "yes") == "yes":
        cmd.append("--no-cpu-affinity")
    return cmd


_RUN_ID_RE = re.compile(
    r"Run created:\s*([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)


def register_run(cli_bin: str, run_dir: Path, dry_run: bool) -> str | None:
    cmd = [cli_bin, "runs", "create", "--path", str(run_dir)]
    if dry_run:
        cmd.append("--dry-run")
    _log("  $ " + " ".join(shlex.quote(c) for c in cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    if proc.returncode != 0:
        raise RuntimeError(f"runs create failed for {run_dir} (rc={proc.returncode})")
    if dry_run:
        return None
    match = _RUN_ID_RE.search(proc.stdout + proc.stderr)
    if not match:
        raise RuntimeError(f"Could not parse run id from runs create output for {run_dir}")
    return match.group(1)


def create_submission_dry_run(cli_bin: str, run_ids: list[str]) -> int:
    division = _env("MLC_MLPERF_ENDPOINTS_SUB_DIVISION", "standardized")
    scenario = _env("MLC_MLPERF_ENDPOINTS_SUB_SCENARIO", "con")
    availability = _env("MLC_MLPERF_ENDPOINTS_SUB_AVAILABILITY", "available")
    cmd = [cli_bin, "submissions", "create", "--division", division,
           "--scenario", scenario, "--availability", availability, "--dry-run"]
    for rid in run_ids:
        cmd += ["--run-ids", rid]
    _log("  $ " + " ".join(shlex.quote(c) for c in cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def main() -> int:
    ep_python = _env("MLC_MLPERF_ENDPOINTS_PYTHON_BIN")
    cli_bin = _env("MLC_MLPERF_ENDPOINTS_CLI_BIN")
    cli_python = _env("MLC_MLPERF_ENDPOINTS_CLI_PYTHON_BIN")
    system_desc = _env("MLC_MLPERF_ENDPOINTS_SYSTEM_DESC_PATH")
    output_dir = Path(_env("MLC_MLPERF_ENDPOINTS_SUB_OUTPUT_DIR")).resolve()
    short_run = _env("MLC_MLPERF_ENDPOINTS_SUB_SHORT_RUN", "no") == "yes"
    runs_dry_run = _env("MLC_MLPERF_ENDPOINTS_SUB_RUNS_DRY_RUN", "no") == "yes"

    for label, val in [("benchmark python", ep_python), ("submission cli", cli_bin),
                       ("system_desc.json", system_desc)]:
        if not val or not Path(val).exists():
            _log(f"ERROR: {label} not found: {val!r}")
            return 1

    with open(system_desc) as f:
        m = int(json.load(f)["max_supported_concurrency"])

    info = get_region_info(cli_python, m)
    regions = info["regions"]
    min_duration_ms = info["min_duration_ms"]

    explicit = []
    raw = _env("MLC_MLPERF_ENDPOINTS_SUB_CONCURRENCIES")
    if raw:
        explicit = [int(x) for x in re.split(r"[,\s]+", raw) if x]
    num_points = int(_env("MLC_MLPERF_ENDPOINTS_SUB_NUM_POINTS", "7"))
    points = select_points(regions, num_points, explicit or None)

    _log("")
    _log(f"Maximum Supported Concurrency (M): {m}")
    for name in REGION_ORDER:
        s, e = regions[name]
        _log(f"  {name:<16} {s}-{e}")
    _log(f"Concurrency points: {points}")
    _log(f"Short run: {short_run}   Runs dry-run (no upload): {runs_dry_run}")

    # Accuracy is measured once per (system, model). Attach it to the first
    # (lowest-concurrency) point via --mode both; that point's results.json then
    # carries accuracy_scores, which the submission builder turns into accuracy/.
    accuracy_enabled = (
        _env("MLC_MLPERF_ENDPOINTS_SUB_WITH_ACCURACY", "no") == "yes"
        or bool(_env("MLC_MLPERF_ENDPOINTS_SUB_ACC_DATASET_PATH")))
    accuracy_idx = 0
    if accuracy_enabled:
        _log(f"Accuracy: measured on point {points[accuracy_idx]} (--mode both).")
    else:
        _log("Accuracy: not configured (submission will lack accuracy/ — pass "
             "--accuracy_dataset or use _with-accuracy).")
    _log("")

    # Classify each point to pick its minimum duration (full run) or the short
    # duration (smoke test).
    short_duration = _env("MLC_MLPERF_ENDPOINTS_SUB_DURATION", "15s")

    def region_of(c: int) -> str:
        for name in REGION_ORDER:
            s, e = regions[name]
            if s <= c <= e:
                return name
        return "high_throughput"

    # Optional bundled echo server for local testing.
    echo_proc = None
    if _env("MLC_MLPERF_ENDPOINTS_SUB_USE_ECHO_SERVER", "no") == "yes":
        port = _env("MLC_MLPERF_ENDPOINTS_SUB_ECHO_PORT", "8765")
        echo_log = output_dir / "echo_server.log"
        output_dir.mkdir(parents=True, exist_ok=True)
        _log(f"Starting bundled echo server on port {port}")
        echo_proc = subprocess.Popen(
            [ep_python, "-m", "inference_endpoint.testing.echo_server", "--port", port],
            stdout=open(echo_log, "w"), stderr=subprocess.STDOUT)
        # wait for readiness
        ready = False
        for _ in range(60):
            if echo_proc.poll() is not None:
                _log("ERROR: echo server exited early"); return 1
            probe = subprocess.run(
                [ep_python, "-c",
                 f"import socket,sys;s=socket.socket();s.settimeout(0.5);"
                 f"sys.exit(0 if s.connect_ex(('127.0.0.1',{int(port)}))==0 else 1)"])
            if probe.returncode == 0:
                ready = True
                break
            time.sleep(0.5)
        if not ready:
            _log("ERROR: echo server did not become ready"); return 1

    try:
        run_ids: list[str] = []
        for idx, c in enumerate(points):
            region = region_of(c)
            duration = short_duration if short_run else _fmt_ms(min_duration_ms.get(region, 600_000))
            run_dir = output_dir / f"point_{c}"
            with_acc = accuracy_enabled and idx == accuracy_idx
            _log(f"[{idx + 1}/{len(points)}] concurrency={c} region={region} "
                 f"duration={duration}{' +accuracy' if with_acc else ''} -> {run_dir}")
            bench_cmd = build_benchmark_cmd(ep_python, c, duration, run_dir,
                                            with_accuracy=with_acc)
            _log("  $ " + " ".join(shlex.quote(x) for x in bench_cmd))
            bproc = subprocess.run(bench_cmd)
            if bproc.returncode != 0:
                _log(f"ERROR: benchmark failed at concurrency {c}")
                return 1
            # Drop the shared system description into the run folder.
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "system_desc.json").write_text(Path(system_desc).read_text())

            rid = register_run(cli_bin, run_dir, runs_dry_run)
            if rid:
                run_ids.append(rid)
                _log(f"  run id: {rid}")
            _log("")
            # Let TIME_WAIT sockets drain before the next point so back-to-back
            # high-concurrency runs don't exhaust local ephemeral ports.
            settle = int(_env("MLC_MLPERF_ENDPOINTS_SUB_SETTLE_SECONDS", "0"))
            if settle and idx < len(points) - 1:
                time.sleep(settle)
    finally:
        if echo_proc is not None:
            echo_proc.terminate()
            try:
                echo_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                echo_proc.kill()

    if runs_dry_run:
        _log("Runs dry-run complete (no uploads, no submission). "
             "Re-run without --runs_dry_run to register runs and assemble a submission.")
        return 0

    if not run_ids:
        _log("ERROR: no runs were registered; cannot create a submission.")
        return 1

    _log("=" * 70)
    _log(f"Registered {len(run_ids)} run(s). Assembling submission (dry-run)…")
    _log("=" * 70)
    rc = create_submission_dry_run(cli_bin, run_ids)

    # Persist the run ids so users can re-use / clean them up.
    (output_dir / "run_ids.json").write_text(json.dumps(run_ids, indent=2))
    _log(f"\nRun IDs written to {output_dir / 'run_ids.json'}")

    if rc != 0:
        if short_run:
            _log("\n[SHORT RUN] submissions create --dry-run reported compliance "
                 "gaps (expected: short runs do not meet duration / sample-count / "
                 "accuracy gates). The end-to-end plumbing executed successfully.")
            return 0
        _log("\nSubmission checker reported errors (see above). Not submission-valid.")
        return rc
    _log("\nSubmission dry-run passed the checker.")
    return 0


def _fmt_ms(ms: int) -> str:
    return f"{int(ms) // 1000}s"


if __name__ == "__main__":
    sys.exit(main())
