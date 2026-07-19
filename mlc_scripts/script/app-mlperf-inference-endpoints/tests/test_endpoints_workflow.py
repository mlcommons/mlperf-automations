# SPDX-License-Identifier: Apache-2.0
"""End-to-end workflow tests for the inference-endpoint MLC integration.

These exercise the *combined* functionality of the automation scripts and the
inference-endpoint package against the bundled echo server (the ``_echo-server``
variation), so no real model or remote server is required.

Each test runs the real ``mlcr`` command line a submitter would use and then
asserts on the ``results.json`` the benchmark produces.

Prerequisites:
  * ``mlcr`` (mlcflow) on PATH.
  * The mlperf-automations repo registered with MLC.
  * Network access on the first run only (to install the package from the local
    source into a dedicated venv); cached thereafter.

Run with:
    pytest -q script/app-mlperf-inference-endpoints/tests/test_endpoints_workflow.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

# Repo layout: <repo>/script/app-mlperf-inference-endpoints/tests/<this file>
REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = REPO_ROOT.parent
# The inference-endpoint source checkout used for the isolated install. Allow an
# override so the suite is portable across machines.
ENDPOINTS_SRC = Path(
    os.environ.get("ENDPOINTS_SRC", WORKSPACE_ROOT / "endpoints")
)

pytestmark = pytest.mark.integration


def _require_mlcr() -> str:
    mlcr = shutil.which("mlcr")
    if mlcr is None:
        pytest.skip("mlcr (mlcflow) is not on PATH")
    return mlcr


# A small worker count keeps each echo-server run light: the default (-1=auto)
# pre-establishes hundreds of TCP connections per worker, and several back-to-back
# benchmarks can otherwise exhaust the local ephemeral-port range (notably on macOS).
ECHO_WORKERS = "2"


@pytest.fixture(autouse=True)
def _settle():
    """Let TIME_WAIT sockets drain between heavy connection benchmarks."""
    yield
    time.sleep(2)


def _run_workflow(variations: str, report_dir: Path, **inputs: str) -> dict:
    """Run `mlcr app,mlperf,inference,endpoints,<variations>` and load results.json."""
    mlcr = _require_mlcr()
    cmd = [mlcr, f"app,mlperf,inference,endpoints,{variations}",
           f"--report_dir={report_dir}", "--quiet"]
    if ENDPOINTS_SRC.is_dir():
        cmd.append(f"--endpoints_src={ENDPOINTS_SRC}")
    for key, value in inputs.items():
        cmd.append(f"--{key}={value}")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, (
        f"workflow failed (rc={proc.returncode})\n"
        f"CMD: {' '.join(cmd)}\n"
        f"STDOUT tail:\n{proc.stdout[-3000:]}\n"
        f"STDERR tail:\n{proc.stderr[-3000:]}"
    )

    results_file = report_dir / "results.json"
    assert results_file.is_file(), f"results.json not produced at {results_file}"
    with open(results_file) as f:
        return json.load(f)


def _assert_clean_perf(data: dict, expected_mode: str) -> dict:
    results = data["results"]
    assert data["config"]["mode"] == expected_mode
    assert results["total"] > 0
    assert results["qps"] > 0
    assert results["successful"] + results["failed"] == results["total"]
    # The workflow is the unit under test, not the host's socket capacity.
    # Running several heavy benchmarks back-to-back against localhost can
    # transiently exhaust ephemeral ports (errno 49 on macOS), failing a few
    # requests. Require a high success rate rather than a brittle 100%.
    success_rate = results["successful"] / results["total"]
    assert success_rate >= 0.95, (
        f"success rate {success_rate:.3f} too low "
        f"({results['successful']}/{results['total']})"
    )
    return results


# Each test uses a distinct echo-server port so sequential runs never collide on
# a lingering socket / TIME_WAIT from the previous test.
def test_offline_echo_server(tmp_path: Path):
    """Offline (max-throughput) benchmark against the echo server."""
    data = _run_workflow("_offline,_echo-server", tmp_path / "offline",
                         num_samples="50", echo_server_port="8771",
                         num_workers=ECHO_WORKERS)
    _assert_clean_perf(data, expected_mode="perf")


def test_online_poisson_echo_server(tmp_path: Path):
    """Online sustained-QPS (Poisson) benchmark against the echo server."""
    data = _run_workflow("_online,_poisson,_echo-server", tmp_path / "poisson",
                         target_qps="50", duration="5s", num_samples="200",
                         echo_server_port="8772", num_workers=ECHO_WORKERS)
    _assert_clean_perf(data, expected_mode="perf")


def test_online_fixed_concurrency_echo_server(tmp_path: Path):
    """Online fixed-concurrency benchmark against the echo server."""
    data = _run_workflow(
        "_online,_fixed-concurrency,_echo-server", tmp_path / "concurrency",
        concurrency="8", duration="5s", num_samples="200",
        echo_server_port="8773", num_workers=ECHO_WORKERS)
    _assert_clean_perf(data, expected_mode="perf")


def _generate_conf(out_path: Path, **inputs: str) -> dict:
    """Run `mlcr generate,mlperf,endpoints-conf` and load the generated YAML."""
    import yaml

    mlcr = _require_mlcr()
    cmd = [mlcr, "generate,mlperf,endpoints-conf",
           f"--conf_path={out_path}", "--quiet"]
    for key, value in inputs.items():
        cmd.append(f"--{key}={value}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, (
        f"config generation failed (rc={proc.returncode})\n"
        f"CMD: {' '.join(cmd)}\nSTDERR tail:\n{proc.stderr[-2000:]}"
    )
    assert out_path.is_file(), f"config not generated at {out_path}"
    with open(out_path) as f:
        return yaml.safe_load(f)


def test_generate_offline_config_predefined_dataset(tmp_path: Path):
    """Offline config with a predefined dataset name (no path)."""
    conf = _generate_conf(
        tmp_path / "offline.yaml", conf_type="offline",
        model="meta-llama/Llama-3.1-8B-Instruct",
        dataset_name="cnn_dailymail", dataset_preset="llama3_8b",
        num_samples="1000")
    assert conf["type"] == "offline"
    assert conf["datasets"][0]["name"] == "cnn_dailymail::llama3_8b"
    assert conf["datasets"][0]["type"] == "performance"
    assert conf["settings"]["load_pattern"]["type"] == "max_throughput"


def test_generate_submission_config(tmp_path: Path):
    """Submission config carries a ruleset reference and perf + accuracy datasets."""
    conf = _generate_conf(
        tmp_path / "submission.yaml", conf_type="submission",
        benchmark_mode="offline", submission_model="llama2-70b",
        ruleset="mlperf-inference-v5.1",
        model="meta-llama/Llama-2-70B-Chat-HF",
        dataset_name="open_orca", num_samples="5000",
        accuracy_dataset_name="gpqa", accuracy_samples="500",
        eval_method="exact_match")
    assert conf["type"] == "submission"
    assert conf["submission_ref"] == {
        "model": "llama2-70b", "ruleset": "mlperf-inference-v5.1"}
    types = sorted(d["type"] for d in conf["datasets"])
    assert types == ["accuracy", "performance"]


def test_app_from_config_chained_echo_server(tmp_path: Path):
    """The _from-config variation generates a config and runs it end-to-end."""
    dataset = ENDPOINTS_SRC / "tests" / "assets" / "datasets" / "dummy_1k.jsonl"
    data = _run_workflow(
        "_from-config,_echo-server", tmp_path / "fromconfig",
        model="test-model", dataset=str(dataset), prompt_column="text_input",
        endpoints="http://localhost:8775", echo_server_port="8775",
        num_samples="50", num_workers=ECHO_WORKERS)
    _assert_clean_perf(data, expected_mode="perf")


def test_online_poisson_requires_target_qps(tmp_path: Path):
    """A poisson run without --target_qps must fail with a clear error."""
    mlcr = _require_mlcr()
    report_dir = tmp_path / "negative"
    cmd = [mlcr, "app,mlperf,inference,endpoints,_online,_poisson,_echo-server",
           f"--report_dir={report_dir}", "--duration=5s",
           "--echo_server_port=8774", "--quiet"]
    if ENDPOINTS_SRC.is_dir():
        cmd.append(f"--endpoints_src={ENDPOINTS_SRC}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode != 0
    assert "requires --target_qps" in (proc.stdout + proc.stderr)
