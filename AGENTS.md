# AGENTS.md — mlperf-automations

> **⚠️ ARCHITECTURE MIGRATION (Option B, mlc-scripts 2.0.0) — READ FIRST.**
> This repo is now **content-only**. The execution engine that used to live in
> `automation/script/` has **moved into mlcflow** (`mlc/engine/`) and the
> `automation/` directory has been **removed**. Scripts now live under
> **`mlc_scripts/script/<alias>/`** and ship as pip **package data**
> (`pip install mlc-scripts` → importable `mlc_scripts`, path in
> `mlc_scripts.SCRIPTS_DIR`). `setup.py`/`CustomInstallCommand` were removed —
> **no git clone at install time**. `pyproject.toml`: `packages=["mlc_scripts"]`,
> `package-data mlc_scripts=["script/**/*"]`, dep `mlcflow>=2.0.0,<3`. Existing
> scripts run **unmodified** (a compat shim in mlcflow re-exposes `utils`).
> Paths in the sections below that say `automation/script/...` or `script/<alias>`
> now map to `mlc_scripts/script/<alias>`. See `migration-modification-plan.md`
> and `MIGRATION-REMOTE-TESTS-README.md` in the parent `MLC/repos/` directory.

Authoritative reference for AI agents and contributors working in this repository.
Every claim is marked with its evidence source or noted as inferred.

---

## Project overview

**Evidence:** `README.md`, `pyproject.toml`, `automation/script/meta.json`

`mlperf-automations` (PyPI: `mlc-scripts` v1.1.0) is the **content layer** — 377+ portable
automation scripts for MLPerf benchmarking. It is not a standalone tool. A separate CLI
driver, `mlcflow` (v1.2.4), discovers and executes scripts from this repo.

**What it does:**
- Runs MLPerf Inference benchmarks across AMD, Intel, NVIDIA, Qualcomm hardware
- Benchmarks LLM/API endpoints (`app-mlperf-inference-endpoints` family)
- Installs and manages benchmark dependencies (datasets, models, compilers, runtimes)
- Generates MLPerf submission packages and system descriptions
- Provides reproducible, cache-aware execution across OS/container environments

---

## Architecture

**Evidence:** `flow.md`, `automation/script/module.py`, `mlcflow/mlc/script_action.py`

### Component map

```
mlcflow CLI  (mlcr / mlcd / mlca / mlct / mlcp / mlce / mlcrr)
    │
    ├── action.py          — base Action, repo registry, item index
    ├── script_action.py   — auto-pulls mlperf-automations if missing;
    │                        dynamically loads automation/script/module.py
    └── repo_action.py     — git clone / pull repos into ~/MLC/repos/
         │
         └──▶ ~/MLC/repos/mlcommons@mlperf-automations/
                  ├── automation/script/
                  │   ├── module.py          — ScriptAutomation (6,207 lines)
                  │   ├── cache_utils.py     — cache lookup / store (18,555 lines)
                  │   ├── docker.py          — Docker container execution
                  │   ├── apptainer.py       — Apptainer/Singularity execution
                  │   ├── remote_run.py      — SSH remote execution
                  │   ├── experiment.py      — experiment/hyperparameter exploration
                  │   ├── meta_schema.py     — YAML schema validator
                  │   ├── lint.py            — meta.yaml key-order fixer
                  │   └── script_utils.py    — script search & selection
                  │
                  └── script/                — 377+ individual automation scripts
                      ├── app-mlperf-inference-endpoints/
                      ├── get-mlperf-endpoints/
                      ├── detect-os/
                      └── … (app-*, get-*, benchmark-*, detect-*, build-*, …)
```

### Key environmental paths

| Path | Purpose |
|---|---|
| `~/MLC/repos/` | Default repo root (override: `MLC_REPOS` env var) |
| `~/MLC/repos/mlcommons@mlperf-automations/` | Where mlcflow clones this repo |
| `~/MLC/repos/local/cache/{uid}/` | Per-script cached outputs |
| `~/MLC/repos/local/cache/{uid}/mlc-cached-state.json` | Cached env + state snapshot |
| `~/MLC/repos/local/cache/{uid}/ml-run-script-versions.json` | Version provenance |

---

## Execution lifecycle (one script run)

**Evidence:** `automation/script/module.py` (full `_run` method)

When `mlcr app,mlperf,inference,endpoints,_offline,_echo-server --num_samples=50` runs:

```
1.  TAG PARSING
    "app,mlperf,inference,endpoints" → script tags
    "_offline", "_echo-server"       → variation tags (underscore stripped)
    Negative tags: -tag excludes scripts with that tag

2.  SCRIPT DISCOVERY
    Index search: find script whose meta.yaml tags superset the requested tags
    Ambiguous match → user prompted; --quiet picks first match

3.  VARIATION RESOLUTION (order matters)
    For each _variation tag:
      a. Apply env from variations.<name>.env
      b. Merge variations.<name>.deps into dep list
      c. Activate variations.<name>.docker / .versions if present
    Groups enforce mutual exclusivity (only one variation per group active)
    Base variations: if variation has base: [other_var], apply other_var first
    Combined variations: key "var1,var2" activates only when both are present

4.  default_env INJECTION
    Merge meta.yaml default_env → env dict (variation env takes precedence)

5.  input_mapping APPLICATION
    CLI --key=val → env[MAPPED_VAR] = val (for every key in input_mapping)

6.  VERSION RESOLUTION
    --version=X → MLC_VERSION=X; version_min/max constraints evaluated

7.  CACHE LOOKUP
    Key: script UID + active env snapshot (new_env_keys + new_state_keys)
    HIT → return cached new_env immediately (skip all remaining steps)
    HIT + dynamic deps → re-execute only dynamic-marked deps, skip the rest
    MISS → continue to step 8

8.  predeps / prehook_deps EXECUTION
    Each dep is a recursive _run() call with current env as input
    Dep env delta (new_env_keys) merged back before next dep runs

9.  preprocess(i) CALL (customize.py)
    Receives mutable env dict; script validates inputs & builds command strings
    return {'return': 1, 'error': '...'} aborts the entire chain

10. deps EXECUTION (same as step 8 but after preprocess)

11. run.sh / run.bat EXECUTION
    Full env dict exported as shell variables
    Must exit 0 on success; non-zero treated as failure

12. posthook_deps / post_deps EXECUTION

13. postprocess(i) CALL (customize.py)
    Parses output files; populates env keys declared in new_env_keys

14. CACHE WRITE
    ~/MLC/repos/local/cache/{uid}/mlc-cached-state.json stores new_env + new_state
    ml-run-script-versions.json records version provenance of all deps

15. ENV DELTA RETURN
    Only keys declared in new_env_keys propagate to the calling script/user
```

---

## Script anatomy

**Evidence:** All scripts in `script/`; `automation/script/meta_schema.py`

Every script lives in `script/<alias>/` with these files:

| File | Role | Required |
|---|---|---|
| `meta.yaml` | Identity, tags, deps, variations, env mapping | YES |
| `customize.py` | `preprocess()`, `postprocess()`, optional hooks | YES (even if only `return {'return':0}`) |
| `run.sh` | Unix/macOS bash execution script | YES on Unix |
| `run.bat` | Windows batch execution script | YES on Windows |
| `README.md` | Documentation (auto-published to docs site) | Strongly recommended |
| `tests/` | pytest integration tests | Recommended |
| `validate_cache.sh` | Shell script to re-validate a cached entry | Optional |

### meta.yaml — full key reference

**Evidence:** `automation/script/meta_schema.py`, `script/app-mlperf-inference-mlcommons-python/meta.yaml`

All examples below are taken verbatim from `script/app-mlperf-inference-mlcommons-python`, the canonical multi-backend MLPerf reference implementation script. It exercises every key the schema supports.

```yaml
# ── Identity (all four required) ──────────────────────────────────────────────
alias: app-mlperf-inference-mlcommons-python   # kebab-case; unique across repo
uid: ff149e9781fc4b65                          # 16 lowercase hex chars; never change
automation_alias: script                       # always "script"
automation_uid: 5b4e0237da074764               # UID of the 'script' automation type; same for all scripts

# ── Discovery ─────────────────────────────────────────────────────────────────
category: MLPerf Inference
tags:
- app
- vision
- language
- mlcommons
- mlperf
- inference
- reference
- ref

# ── Environment ───────────────────────────────────────────────────────────────
default_env:                            # lowest-priority; variation env overrides these
  MLC_MLPERF_LOADGEN_MODE: accuracy
  MLC_MLPERF_LOADGEN_SCENARIO: Offline
  MLC_OUTPUT_FOLDER_NAME: test_results
  MLC_MLPERF_RUN_STYLE: test
  MLC_TEST_QUERY_COUNT: '10'
  MLC_MLPERF_QUANTIZATION: false
  MLC_MLPERF_SUT_NAME_IMPLEMENTATION_PREFIX: reference
  MLC_MLPERF_SUT_NAME_RUN_CONFIG_SUFFIX: ''

new_env_keys:                           # ONLY keys matching these patterns propagate to callers
  - MLC_MLPERF_*
  - MLC_DATASET_*
  - MLC_HW_NAME
  - MLC_ML_MODEL_*
  - MLC_MAX_EXAMPLES
  - MLC_VLLM_*

new_state_keys:                         # persistent state written into the MLC state dict (not env)
  - mlperf-inference-implementation
  - MLC_SUT_*

env_key_mappings:                       # strip a prefix before passing env to the subprocess
  MLC_HOST_: HOST_                      # MLC_HOST_OS_TYPE → HOST_OS_TYPE in run.sh
  MLC_ML_: ML_
  MLC_MLPERF_TVM: MLPERF_TVM
  MLC_MLPERF_DELETE: MLPERF_DELETE

# ── Input mapping ─────────────────────────────────────────────────────────────
# CLI: mlcr app,mlperf,inference,reference --mode=performance --scenario=Offline
# Each --key=val is translated to the corresponding env var before preprocess runs.
input_mapping:
  clean: MLC_MLPERF_CLEAN_SUBMISSION_DIR
  count: MLC_MLPERF_LOADGEN_QUERY_COUNT
  dataset: MLC_MLPERF_VISION_DATASET_OPTION
  hw_name: MLC_HW_NAME
  max_batchsize: MLC_MLPERF_LOADGEN_MAX_BATCHSIZE
  mode: MLC_MLPERF_LOADGEN_MODE
  network: MLC_NETWORK_LOADGEN
  num_threads: MLC_NUM_THREADS
  offline_target_qps: MLC_MLPERF_LOADGEN_OFFLINE_TARGET_QPS
  output_dir: OUTPUT_BASE_DIR
  power: MLC_MLPERF_POWER
  rerun: MLC_RERUN
  scenario: MLC_MLPERF_LOADGEN_SCENARIO
  server_target_qps: MLC_MLPERF_LOADGEN_SERVER_TARGET_QPS
  target_qps: MLC_MLPERF_LOADGEN_TARGET_QPS
  test_query_count: MLC_TEST_QUERY_COUNT
  threads: MLC_NUM_THREADS

# ── Dependencies ─────────────────────────────────────────────────────────────
# deps: run BEFORE preprocess(). Evaluated top-to-bottom; conditions checked at runtime.
deps:
  # Unconditional — always run regardless of variations
  - tags: detect,os
  - tags: detect,cpu
  - tags: get,sys-utils-mlc
  - tags: get,python
    names:
    - python                            # stable handles used by add_deps_recursive
    - python3

  # Conditional on env — only install CUDA if device=gpu AND backend needs it
  - tags: get,cuda,_cudnn
    names:
    - cuda
    enable_if_env:                      # ALL keys must match (AND logic)
      MLC_MLPERF_DEVICE:
      - gpu
      MLC_MLPERF_BACKEND:
      - onnxruntime
      - tf
      - tflite
      - pytorch

  # GPU onnxruntime — skip for models that use CPU onnxruntime even on GPU hosts
  - tags: get,generic-python-lib,_onnxruntime_gpu
    names:
    - ml-engine-onnxruntime-cuda
    enable_if_env:
      MLC_MLPERF_BACKEND:
      - onnxruntime
      - tvm-onnx
      MLC_MLPERF_DEVICE:
      - gpu
    skip_if_env:                        # skip if env[KEY] matches any listed value
      MLC_MODEL:
      - 3d-unet-99
      - 3d-unet-99.9
      - resnet50

  # skip_if_any_env: skip if ANY of the listed vars matches (OR logic across keys)
  - tags: get,ml-model,stable-diffusion,text-to-image,sdxl
    names:
    - ml-model
    - sdxl-model
    enable_if_env:
      MLC_MODEL:
      - stable-diffusion-xl
    skip_if_any_env:                    # skip if MLC_MLPERF_CUSTOM_MODEL_PATH OR docker state is set
      MLC_MLPERF_CUSTOM_MODEL_PATH:
      - 'on'
    skip_if_env:
      MLC_RUN_STATE_DOCKER:
      - 'yes'
      MLC_MLPERF_MODEL_SDXL_DOWNLOAD_TO_HOST:
      - 'yes'

  # update_tags_from_env_with_prefix — inject env value into dep tag at runtime
  # e.g. MLC_MODEL=resnet50 → adds tag "_model.resnet50" to the tvm-model dep
  - tags: get,tvm-model,_onnx
    names:
    - tvm-model
    update_tags_from_env_with_prefix:
      _model.:                          # prefix
      - MLC_MODEL                       # env var whose value is appended

  # env: — set extra env vars just for this one dep (not inherited by others)
  - tags: get,generic-python-lib,_onnxruntime_gpu
    env:
      MLC_GENERIC_PYTHON_PIP_UNINSTALL_DEPS: ''
    enable_if_env:
      MLC_MLPERF_BACKEND:
      - onnxruntime
      MLC_MLPERF_DEVICE:
      - gpu
      MLC_MODEL:
      - 3d-unet-99
      - resnet50

  # Model deps — each guarded by enable_if_env on MLC_MODEL
  - tags: get,ml-model,image-classification,resnet50
    names: [ml-model, resnet50-model]
    enable_if_env:
      MLC_MODEL: [resnet50]
    skip_if_env:
      MLC_MLPERF_CUSTOM_MODEL_PATH: ['on']

  - tags: get,ml-model,language-processing,bert-large
    names: [ml-model, bert-model]
    enable_if_env:
      MLC_MODEL: [bert-99, bert-99.9]

  # LoadGen and inference source — always required
  - tags: get,loadgen,_wg-inference
    names: [loadgen, mlperf-inference-loadgen]
  - tags: get,mlcommons,inference,src
    names: [inference-src]

  # Two deps sharing the same name — second overrides env for that copy
  - tags: get,mlcommons,inference,src
    env:
      MLC_GET_MLPERF_IMPLEMENTATION_ONLY: 'yes'
    names: [mlperf-implementation]

# run AFTER preprocess(), before run.sh
prehook_deps:
  - names: [remote-run-cmds]
    tags: remote,run,cmds
    enable_if_env:
      MLC_ASSH_RUN_COMMANDS: ['on']

# run AFTER run.sh, before postprocess()
posthook_deps:
  - names: [mlperf-runner]
    tags: benchmark-mlperf
    skip_if_env:
      MLC_MLPERF_SKIP_RUN: ['on']

# run AFTER postprocess()
post_deps:
  - tags: save,mlperf,inference,state
    names: [save-mlperf-inference-state]

# ── Variations ────────────────────────────────────────────────────────────────
variations:

  # ── device group (mutually exclusive) ─────────────────────────────────────
  cpu:
    group: device
    default: true                       # selected when no device variation is given
    env:
      MLC_MLPERF_DEVICE: cpu
      CUDA_VISIBLE_DEVICES: ''
      USE_CUDA: false
      USE_GPU: false

  cuda:
    group: device
    env:
      MLC_MLPERF_DEVICE: gpu
      USE_CUDA: true
      USE_GPU: true

  rocm:
    group: device
    env:
      MLC_MLPERF_DEVICE: rocm
      USE_GPU: true

  # ── framework group ────────────────────────────────────────────────────────
  onnxruntime:
    group: framework
    default: true
    add_deps_recursive:                 # propagate tag overrides to named deps deep in the subtree
      imagenet-preprocessed:
        tags: _NCHW
      openimages-preprocessed:
        tags: _NCHW
      ml-model:
        tags: raw,_onnx
      numpy:
        version_max: 1.26.4
        version_max_usable: 1.26.4
    env:
      MLC_MLPERF_BACKEND: onnxruntime

  pytorch:
    group: framework
    add_deps_recursive:
      imagenet-preprocessed:
        tags: _NCHW
      ml-model:
        tags: raw,_pytorch
    env:
      MLC_MLPERF_BACKEND: pytorch
      MLC_MLPERF_BACKEND_VERSION: <<<MLC_TORCH_VERSION>>>   # template: resolved at runtime from env

  vllm:
    group: framework
    env:
      MLC_MLPERF_BACKEND: vllm

  tvm-onnx:
    group: framework
    env:
      MLC_MLPERF_BACKEND: tvm-onnx
      MLC_MLPERF_BACKEND_VERSION: <<<MLC_ONNXRUNTIME_VERSION>>>
    deps:                               # extra deps active only when this variation is selected
    - tags: get,generic-python-lib,_onnx
    - tags: get,tvm
      names: [tvm]
    - tags: get,tvm-model,_onnx
      names: [tvm-model]
      update_tags_from_env_with_prefix:
        _model.:
        - MLC_MODEL

  # ── model group ────────────────────────────────────────────────────────────
  resnet50:
    group: models
    default: true
    env:
      MLC_MODEL: resnet50
      MLC_MLPERF_USE_MLCOMMONS_RUN_SCRIPT: 'yes'
    deps:
    - tags: get,generic-python-lib,_opencv-python
      version_max: 4.10.0.82
    - tags: get,generic-sys-util,_libgl
    - tags: get,generic-python-lib,_numpy
      names: [numpy]
      version_max: 1.26.4
    - tags: get,generic-python-lib,_pycocotools
    prehook_deps:                       # variation-level prehook_deps, merged with script-level
    - tags: get,generic-python-lib,_protobuf
      names: [protobuf]
      version_min: 3.20.3
      enable_if_env:
        MLC_MLPERF_BACKEND: [tf, tflite]

  bert-99:
    group: models
    base:                               # apply the 'bert' (non-group) variation first, then this
    - bert
    env:
      MLC_MODEL: bert-99

  bert-99.9:
    group: models
    base:
    - bert
    env:
      MLC_MODEL: bert-99.9

  llama2-70b-99:
    group: models
    base:
    - llama2-70b_
    env:
      MLC_MODEL: llama2-70b-99

  llama3_1-405b:
    group: models
    env:
      MLC_MODEL: llama3_1-405b
    adr:                                # adr inside a variation: overrides specific named deps
      pytorch:
        version_max: 2.5.1
      vllm:
        env:
          MLC_GENERIC_PYTHON_PIP_EXTRA: --upgrade
    deps:
    - tags: get,generic-python-lib,_package.transformers
    - tags: get,generic-python-lib,_package.sentencepiece
    - tags: get,generic-python-lib,_package.accelerate
    - tags: get,generic-python-lib,_package.pandas
      version_max: 2.2.1

  # ── base (non-group) variations — apply shared config, referenced via base: ──
  # These have no group: so they cannot be selected directly on the CLI.
  bert:
    env:
      MLC_MLPERF_MODEL_SKIP_BATCHING: true
    deps:
    - tags: get,generic-python-lib,_tokenization
    - tags: get,generic-python-lib,_boto3
      enable_if_env:
        MLC_MLPERF_BACKEND: [pytorch]
    add_deps_recursive:
      inference-src:
        tags: _deeplearningexamples

  llama2-70b_:
    env:
      MLC_MLPERF_MODEL_SKIP_BATCHING: false
    deps:
    - tags: get,generic-python-lib,_package.transformers
      names: [transformers]
    - tags: get,generic-python-lib,_package.sentencepiece
      names: [sentencepiece]
    - tags: get,generic-python-lib,_package.nltk
      names: [nltk]
      version_max: 3.8.1
      version_max_usable: 3.8.1

  # ── precision group ────────────────────────────────────────────────────────
  fp32:
    group: precision
    default: true
    add_deps_recursive:
      ml-model:
        tags: _fp32
    env:
      MLC_MLPERF_QUANTIZATION: false
      MLC_MLPERF_MODEL_PRECISION: float32

  int8:
    group: precision
    env:
      MLC_MLPERF_QUANTIZATION: true
      MLC_MLPERF_MODEL_PRECISION: int8
    add_deps_recursive:
      ml-model:
        tags: _int8

  float16:
    group: precision
    add_deps_recursive:
      ml-model-float16:
        tags: _fp16
    env:
      MLC_MLPERF_QUANTIZATION: false
      MLC_MLPERF_MODEL_PRECISION: float16

  # ── alias — redirect one name to another variation ─────────────────────────
  quantized:
    alias: int8                         # mlcr ...,_quantized is identical to ...,_int8

  tensorflow:
    alias: tf

  # ── scenario group ─────────────────────────────────────────────────────────
  offline:
    env:
      MLC_MLPERF_LOADGEN_SCENARIO: Offline
  server:
    env:
      MLC_MLPERF_LOADGEN_SCENARIO: Server
  singlestream:
    env:
      MLC_MLPERF_LOADGEN_SCENARIO: SingleStream
  multistream:
    env:
      MLC_MLPERF_LOADGEN_SCENARIO: MultiStream

  # ── dynamic variation — _batch_size.64 sets MLC_MLPERF_LOADGEN_MAX_BATCHSIZE=64 ─
  batch_size.#:
    group: batch-size
    env:
      MLC_MLPERF_LOADGEN_MAX_BATCHSIZE: '#'   # '#' is substituted with the suffix from the tag
    add_deps_recursive:
      ml-model:
        tags: _batch_size.#
      tvm-model:
        tags: _batch_size.#

  # ── combined variations — only active when BOTH named variations are selected ─
  # Key is comma-separated; order matches the CLI invocation order.
  onnxruntime,cpu:
    env:
      MLC_MLPERF_BACKEND_VERSION: <<<MLC_ONNXRUNTIME_VERSION>>>

  onnxruntime,cuda:
    env:
      MLC_MLPERF_BACKEND_VERSION: <<<MLC_ONNXRUNTIME_GPU_VERSION>>>
      ONNXRUNTIME_PREFERRED_EXECUTION_PROVIDER: CUDAExecutionProvider

  onnxruntime,rocm:
    add_deps_recursive:
      onnxruntime:
        tags: _rocm
    env:
      ONNXRUNTIME_PREFERRED_EXECUTION_PROVIDER: ROCMExecutionProvider

  llama2-70b_,cuda:
    default_env:
      MLC_MLPERF_LOADGEN_MAX_BATCHSIZE: 8

  deepseek-r1,pytorch:
    deps:
    - tags: get,generic-python-lib,_package.triton
    - tags: get,generic-python-lib,_package.transformers
    - tags: get,generic-python-lib,_package.accelerate

  llama3_1-405b,cpu:
    env:
      MLC_GENERIC_PYTHON_PIP_EXTRA_FIND_LINKS_URL: https://data.pyg.org/whl/torch-<<<MLC_TORCH_VERSION>>>+cpu.html

  llama3_1-405b,cuda:
    env:
      MLC_GENERIC_PYTHON_PIP_EXTRA_FIND_LINKS_URL: https://data.pyg.org/whl/torch-<<<MLC_TORCH_VERSION>>>.html

# ── Docker-specific ───────────────────────────────────────────────────────────
docker:
  real_run: false                       # don't run the benchmark inside Docker; only set up env
```

### Template substitution

Inside `run.sh` or meta.yaml docker mounts, use `<<<VAR>>>` or `${{VAR}}` to
inject an env variable's value:

```bash
# run.sh — compose from env pieces set by preprocess
${MLC_PYTHON_BIN} <<<MLC_MLPERF_ENDPOINT_SCRIPT>>> \
  --endpoints <<<MLC_MLPERF_ENDPOINT_URL>>>
```

---

### customize.py — hook reference

**Evidence:** `script/app-mlperf-inference-endpoints/customize.py`,
`script/get-mlperf-endpoints/customize.py`

```python
from mlc import utils
import os, json

def preprocess(i):
    """
    Called before run.sh. Validate inputs; build command; mutate env.
    i['env']        — mutable dict; everything set here goes to run.sh
    i['automation'] — ScriptAutomation; use i['automation'].logger
    i['os_info']    — OS detection result (from detect-os dep)
    i['meta']       — parsed meta.yaml as dict
    i['run_script_input'] — original CLI input dict
    """
    env = i['env']
    logger = i['automation'].logger

    # Guard: required env var must be set by a dependency
    python_bin = env.get('MLC_MLPERF_ENDPOINTS_PYTHON_BIN', '').strip()
    if not python_bin:
        return {'return': 1,
                'error': 'MLC_MLPERF_ENDPOINTS_PYTHON_BIN not set — '
                         'get,mlperf,endpoints dependency failed or was skipped'}

    # Build the shell command; store it in env for run.sh
    cmd = f"{python_bin} -m inference_endpoint.main benchmark offline ..."
    env['MLC_MLPERF_ENDPOINT_CMD'] = cmd
    logger.info(f'Endpoint command: {cmd}')
    return {'return': 0}


def postprocess(i):
    """
    Called after run.sh. Parse outputs; populate new_env_keys.
    """
    env = i['env']
    results_file = os.path.join(env.get('MLC_MLPERF_ENDPOINT_REPORT_DIR', ''),
                                'results.json')
    if os.path.isfile(results_file):
        with open(results_file) as f:
            results = json.load(f)
        env['MLC_MLPERF_ENDPOINT_QPS'] = str(results.get('qps', ''))
        env['MLC_MLPERF_ENDPOINT_RESULTS_FILE'] = results_file
    return {'return': 0}


# Optional additional hooks
def predeps(i):   return {'return': 0}   # before dep execution
def postdeps(i):  return {'return': 0}   # after dep execution
```

**Rules:**
- Never raise exceptions for expected errors; always `return {'return': 1, 'error': '...'}`.
- Use `i['automation'].logger`, not `print()`.
- Declare every env key you set in `new_env_keys` in `meta.yaml`; undeclared keys are silently dropped.
- `MLC_TMP_*` keys are NOT cached and NOT passed to child deps by default.

---

### run.sh contract

```bash
#!/bin/bash
# All env vars from preprocess() are exported into this shell.
# Exit non-zero on failure — the harness checks $?.

eval "${MLC_MLPERF_ENDPOINT_CMD}"
EXIT_CODE=$?
test ${EXIT_CODE} -eq 0 || exit ${EXIT_CODE}
```

- Use `eval` on command-strings assembled in preprocess.
- Do not hard-code paths; reference env vars.
- Return 0 only on verified success.

---

## Environment variable system

**Evidence:** `automation/script/module.py` (env propagation logic)

### Namespace conventions

```
MLC_*                    — global mlcflow variables
MLC_TMP_*                — transient runtime-only; not cached, not passed to deps
MLC_GIT_*                — git-related; not passed to deps unless force_env_keys
MLC_HOST_*               — set by detect-os / detect-cpu
MLC_MLPERF_*             — MLPerf-wide
MLC_MLPERF_ENDPOINT_*    — app-mlperf-inference-endpoints output vars
MLC_MLPERF_ENDPOINTS_*   — get-mlperf-endpoints install vars (the package)
```

### Flow rules

```
CLI input
    │ input_mapping
    ▼
Script env dict  ← default_env ← variation env
    │ (filtered by clean_env_keys, augmented by force_env_keys)
    ▼
Child dep env
    │ (only dep's new_env_keys propagate back)
    ▼
Parent gets dep delta → merged into script env
    │
    ▼
postprocess fills new_env_keys
    │ (only these keys leave the script)
    ▼
Caller receives new_env delta
```

### `+VAR` append syntax in new_env_keys

`+PATH` in `new_env_keys` means "prepend this script's PATH addition to the
existing PATH". The `+` prefix triggers concatenation logic in the engine.

---

## Script categories

**Evidence:** `script/` directory survey (376 scripts)

| Prefix | Count | Purpose |
|---|---|---|
| `get-*` | ~200 | Download/detect/install tools, libs, models, datasets |
| `app-*` | ~34 | Full benchmark runners |
| `get-ml-model-*` | ~15 | Model-specific download scripts |
| `get-dataset-*` | ~15 | Dataset download scripts |
| `get-preprocessed-dataset-*` | ~10 | Pre-processed dataset variants |
| `benchmark-*` | ~9 | Benchmark orchestrators |
| `install-*` | ~6 | System-level installs from source |
| `build-*` | ~4 | Docker/Apptainer/binary builders |
| `detect-*` | 3 | OS, CPU, hardware detection |
| `generate-*` | ~4 | Config/submission file generators |
| `run-*` | ~3 | Thin execution wrappers |
| `reproduce-*` | ~2 | Reproducibility scripts |

### MLPerf Inference script family

The benchmark is a layered call chain. The user invokes `run-mlperf-inference-app`; its `preprocess()` dynamically constructs a tag string and calls `app-mlperf-inference` programmatically for each (scenario, mode) pair; `app-mlperf-inference` dispatches to the right implementation script; that script's `posthook_deps` invoke `benchmark-any-mlperf-inference-implementation` to actually run LoadGen.

```
run-mlperf-inference-app          # user entry point (uid: 4a5d5b13fd7e4ac8)
  └─ preprocess() builds tags:
       app,mlperf,inference,generic,_reference,_resnet50,_onnxruntime,_cpu,_test,_r6.0-dev,_offline
  └─ calls app-mlperf-inference   # implementation dispatcher (uid: d775cac873ee4231)
       └─ deps dispatch based on MLC_MLPERF_IMPLEMENTATION:
            _mlcommons-python → app-mlperf-inference-mlcommons-python  (uid: ff149e9781fc4b65)
            _nvidia            → app-mlperf-inference-nvidia
            _intel             → app-mlperf-inference-intel
            _qualcomm          → app-mlperf-inference-qualcomm
            _mlcommons-cpp     → app-mlperf-inference-mlcommons-cpp
       └─ posthook_deps:
            benchmark-any-mlperf-inference-implementation  # LoadGen runner (uid: 8d3cd46f54464810)
  └─ post_deps (submission variation only):
       generate-mlperf-inference-submission               # packages submission tree (uid: 5f8ab2d0b5874d53)
```

**Key scripts in the family:**

| Script alias | UID | Tags | Role |
|---|---|---|---|
| `run-mlperf-inference-app` | `4a5d5b13fd7e4ac8` | `run,run-mlperf,run-mlperf-inference` | User entry point; orchestrates scenarios × modes loop |
| `app-mlperf-inference` | `d775cac873ee4231` | `app,mlperf,inference,reference` | Dispatches to a named implementation via variations |
| `app-mlperf-inference-mlcommons-python` | `ff149e9781fc4b65` | `app,mlperf,inference,reference,ref` | Reference Python implementation; 40+ model/framework/device variations |
| `app-mlperf-inference-nvidia` | — | `app,mlperf,inference,nvidia` | NVIDIA TensorRT-LLM / custom harness |
| `app-mlperf-inference-intel` | — | `app,mlperf,inference,intel` | Intel-optimised implementation |
| `benchmark-any-mlperf-inference-implementation` | `8d3cd46f54464810` | `benchmark,run,natively,all,inference` | Actual LoadGen runner; called as `posthook_dep` of implementation scripts |
| `generate-mlperf-inference-user-conf` | `3af4475745964b93` | `generate,mlperf,inference,user-conf` | Produces `user.conf` fed to LoadGen |
| `get-mlperf-inference-src` | `4b57186581024797` | `get,src,inference,inference-src` | Clones/caches the MLPerf inference source tree |
| `get-mlperf-inference-loadgen` | `64c3d98d0ba04950` | `get,loadgen,mlperf,mlcommons` | Builds and installs the LoadGen Python bindings |
| `get-mlperf-inference-results-dir` | `84f3c5aad5e1444b` | `get,mlperf,inference,local,results,dir` | Creates versioned results directory; versioned via `_version.r*` tags via adr |
| `save-mlperf-inference-implementation-state` | `b14b813229c444f8` | `save,mlperf,inference,implementation,state` | Persists benchmark state after a run |
| `generate-mlperf-inference-submission` | `5f8ab2d0b5874d53` | `generate,submission,mlperf,mlperf-inference` | Packages logs + system desc into a submission tree |
| `run-mlperf-inference-submission-checker` | `15d03ec2c1af4297` | `run,mlc,mlcommons,mlperf,inference` | Runs the official MLPerf submission checker |
| `preprocess-mlperf-inference-submission` | `c23068394a314266` | `run,mlc,mlcommons,mlperf,inference,submission` | Truncates accuracy logs, normalises structure pre-submission |

**How `run-mlperf-inference-app` picks the right implementation script:**

`preprocess()` reads `MLC_MLPERF_IMPLEMENTATION` (set via `--implementation=mlcommons-python`) and builds a tag string like `app,mlperf,inference,generic,_mlcommons-python,_resnet50,_onnxruntime,_cpu,_test,_r6.0-dev,_offline`. That tag string is passed to `automation.run_script(tags=...)` in a loop over each (scenario, mode) pair. The result maps to `app-mlperf-inference` because that script's tags are a superset of `app,mlperf,inference,generic`.

**Benchmark-version variations in `run-mlperf-inference-app`:**

Each MLPerf round has a named variation (`r4.1`, `r5.0`, `r5.1`, `r6.0-dev`, …). Each sets `MLC_MLPERF_INFERENCE_VERSION` and uses `adr` to point the results-dir, submission-dir, and nvidia-scratch-space deps to the correct versioned cache:

```yaml
  r5.1:
    group: benchmark-version
    env:
      MLC_MLPERF_INFERENCE_VERSION: '5.1'
      MLC_MLPERF_SUBMISSION_CHECKER_VERSION: v5.1
    adr:
      get-mlperf-inference-results-dir:
        tags: _version.r5.1
      get-mlperf-inference-submission-dir:
        tags: _version.r5.1
      mlperf-inference-nvidia-scratch-space:
        tags: _version.r5.1
```

`r6.0-dev` is the current `default: true` variation.

**Submission generation variations:**

The `submission-generation` group controls what modes are run and whether the submission checker fires:

| Variation | Group | What it does |
|---|---|---|
| `find-performance` | submission-generation | Performance mode only; no submission packaging |
| `accuracy-only` | submission-generation | Accuracy mode only |
| `performance-only` | submission-generation | Performance mode only |
| `performance-and-accuracy` *(default)* | submission-generation | Both modes via `all-modes` base |
| `submission` | submission-generation | Both modes + compliance + checker + tar |
| `full` | submission-generation-style | Full dataset (for official submission) |
| `short` *(default)* | submission-generation-style | Reduced dataset, open division |

---

## Commands

**Evidence:** `pyproject.toml` (mlcflow), `.github/workflows/test-mlc-script-features.yml`

### Install

```bash
pip install mlcflow                      # installs mlcr/mlcd/mlca/mlct/mlcp/mlce/mlcrr CLI
pip install mlc-scripts                  # registers this repo's scripts as Python package
# OR (preferred for development):
mlc pull repo mlcommons@mlperf-automations --branch=main
```

### Run a script

```bash
mlcr <comma-separated-tags> [_variation …] [--key=value …] [flags]

# Endpoint benchmark — offline with echo server
mlcr app,mlperf,inference,endpoints,_offline,_echo-server \
     --num_samples=50 --quiet

# Real endpoint — online with Poisson load
mlcr app,mlperf,inference,endpoints,_online,_poisson \
     --endpoints=http://host:8000 \
     --model=llama-3-8b \
     --target_qps=10 \
     --num_samples=200

# From YAML config
mlcr app,mlperf,inference,endpoints,_from-config \
     --config=benchmark.yaml

# Local source checkout instead of cloning
mlcr app,mlperf,inference,endpoints,_echo-server \
     --src=/path/to/inference-endpoint-checkout
```

**Common flags:**

| Flag | Effect |
|---|---|
| `--quiet` / `-s` | Suppress non-error output |
| `--verbose` / `-v` | Debug logging |
| `--new` | Force fresh run (ignore existing cache) |
| `-j` / `--json` | Output result as JSON |
| `--rebuild` | Invalidate and re-run this script's cache |
| `--version=X` | Pin script to version X |
| `--version_min=X` | Minimum version |
| `--version_max=X` | Maximum version |

### Other CLI commands

```bash
# Script management
mlc find script --tags=app,mlperf,inference,endpoints
mlc show script --tags=detect,os
mlc list script
mlc add script mlcommons@mlperf-automations:my-new-script
mlc lint script --tags=app,mlperf,inference,endpoints     # fix meta.yaml key order
mlc doc script --tags=app,mlperf,inference,endpoints      # generate README.md

# Cache management
mlc find cache --tags=get,mlperf,endpoints
mlc show cache --tags=get,mlperf,endpoints
mlc rm cache --tags=get,mlperf,endpoints                  # remove specific cache
mlc rm cache -f                                           # remove ALL caches
mlc prune cache                                           # remove expired entries

# Repo management
mlc pull repo mlcommons@mlperf-automations --branch=main
mlcp mlcommons@mlperf-automations                         # shorthand
mlc list repo
mlc rm repo mlcommons@mlperf-automations

# Container execution
mlcd app,mlperf,inference,endpoints,_echo-server          # Docker
mlca app,mlperf,inference,endpoints                       # Apptainer/Singularity

# Remote execution via SSH
mlcrr app,mlperf,inference,endpoints \
      --remote_host=192.168.1.100 --remote_user=ubuntu \
      --remote_python_venv=mlcflow

# Experiment / hyperparameter exploration
mlce app,mlperf,inference,endpoints \
     --exp.num_samples=50,100,200 --exp.target_qps=5,10,20

# Test built-in tests declared in meta.yaml tests: section
mlct app,mlperf,inference,endpoints
```

### Lint and test

```bash
# Lint meta.yaml (fix key order, validate schema)
mlcr lint,script --tags=app,mlperf,inference,endpoints

# pytest integration tests
pytest -q script/app-mlperf-inference-endpoints/tests/

# Prerequisites for integration tests:
#   - mlcr on PATH
#   - mlperf-automations registered with mlcflow
#   - ENDPOINTS_SRC env var pointing at inference-endpoint source checkout
```

---

## Integration model — adding a new script

**Evidence:** `automation/script/meta_schema.py`,
`script/app-mlperf-inference-endpoints/`

There is **no plugin registry, no decorator, no base class**. Registration is
purely directory + tag based: create `script/<alias>/`, populate the files, and
mlcflow's index finds it automatically.

### Step-by-step

1. **Scaffold** with `mlc add script`:
   ```bash
   # Basic skeleton (copies the template,generic script)
   mlc add script mlcommons@mlperf-automations:<alias> --tags=<tags>

   # Copy nearest existing script as template instead
   mlc add script mlcommons@mlperf-automations:<alias> --tags=<tags> \
       --template_tags=app,mlperf,inference,reference
   ```
   Creates `script/<alias>/` with `meta.yaml`, `customize.py`, and `run.sh`.
   If `--template_tags` matches multiple scripts, it prompts to pick one.
   The UID is auto-generated; verify uniqueness with:
   `grep -r "uid: <generated-uid>" script/ automation/`

2. **Edit `meta.yaml`** — update `alias`, `uid`, `tags`, `category`, `input_mapping`, `new_env_keys`, and `deps`.
3. **Edit `customize.py`** — implement `preprocess(i)` (guard required env vars, build shell command).
4. **Edit `run.sh`** — ensure it evals the command and exits non-zero on failure.
5. **Create `README.md`** — auto-published to docs by CI `document-scripts.yml`.
6. **Add tests** in `script/<alias>/tests/` using real `mlcr` CLI calls.
7. **Add CI workflow** in `.github/workflows/` gating PRs on your script.
8. **Lint**: `mlc lint script --tags=<your-alias>` before committing.

### Dependency chain patterns

**Simple chain:** one script feeds the next via env vars.
```yaml
deps:
  - tags: detect,os                 # sets MLC_HOST_OS_TYPE, MLC_HOST_PLATFORM_FLAVOR
  - tags: get,python3               # sets MLC_PYTHON_BIN_WITH_PATH
  - tags: get,mlperf,endpoints      # sets MLC_MLPERF_ENDPOINTS_PYTHON_BIN
```

**Conditional chain:** dep activates only for specific env values.
```yaml
deps:
  - tags: get,cuda,_cudnn
    enable_if_env:
      MLC_MLPERF_DEVICE: [gpu, cuda]
  - tags: get,rocm
    enable_if_env:
      MLC_MLPERF_DEVICE: [rocm]
```

**Override with ADR:** change a tag in a nested dep from a parent script.
```yaml
# In the parent's meta.yaml, override the "python" dep anywhere in the subtree
add_deps_recursive:
  python:                            # matches deps with names: [python]
    version_max: "3.11.999"
  mlperf-endpoints:
    tags: _online                   # add _online variation to that named dep
```

**Version matrix:** same script, different dep sets per version.
```yaml
default_version: "2.0"
versions:
  "1.0":
    env:
      MLC_GIT_CHECKOUT: v1.0
    deps:
      - tags: get,python3
        version_max: "3.10.999"
  "2.0":
    env:
      MLC_GIT_CHECKOUT: v2.0
    deps:
      - tags: get,python3
        version_min: "3.11"
```

---

## Conventions

**Evidence:** `script/app-mlperf-inference-endpoints/meta.yaml`,
`automation/script/module.py`, `automation/script/meta_schema.py`

### Naming

| Entity | Convention | Example |
|---|---|---|
| Script alias / directory | `kebab-case`, semantic prefix | `app-mlperf-inference-endpoints` |
| Environment variables | `UPPER_SNAKE_CASE` with `MLC_` prefix | `MLC_MLPERF_ENDPOINT_URL` |
| Python functions | `snake_case` | `preprocess`, `postprocess` |
| Python classes | `PascalCase` | `ScriptAutomation` |
| YAML keys | `snake_case` | `input_mapping`, `new_env_keys` |
| UIDs | 16-char lowercase hex | `22926c07f46c4e31` |
| Variation CLI flag | leading underscore | `_offline`, `_echo-server` |

### Script prefix semantics

| Prefix | Meaning |
|---|---|
| `app-` | Full application / benchmark runner |
| `get-` | Download, detect, or install a dependency (often cached) |
| `detect-` | Detect system capabilities (OS, CPU, CUDA, …) |
| `build-` | Compile from source |
| `benchmark-` | Benchmark orchestrators |
| `generate-` | Generate config or submission files |
| `run-` | Thin execution wrappers |
| `install-` | System-level installs |
| `reproduce-` | Reproducibility/auditing scripts |

### Return code pattern

```python
# Success
return {'return': 0}
return {'return': 0, 'new_env': {...}, 'new_state': {...}}

# Error
return {'return': 1, 'error': 'human-readable description'}
return {'return': 16, 'error': 'no scripts found matching tags'}  # specific codes
```

Never raise exceptions for recoverable conditions.

### Logging

```python
logger = i['automation'].logger
logger.info('')                              # blank separator
logger.info(f'Building command: {cmd}')
logger.warning('CPU affinity not supported on macOS; falling back.')
logger.debug('verbose detail')
```

Do not use `print()` in `customize.py`.

### Dependency declarations

Prefer `tags:` lookups over `names:` for finding deps. Use `names:` to give
a dep a stable handle so other scripts can override it via `--dep_name.<handle>.tags=…`
and via `add_deps_recursive`.

```yaml
deps:
  - names: [python, python3]          # stable handle for ADR
    tags: get,python3
  - tags: get,mlperf,endpoints
    names: [mlperf-endpoints]
```

---

## Common pitfalls

**Evidence:** `automation/script/module.py`, `script/app-mlperf-inference-mlcommons-python/customize.py`

### 1. UID collisions

UIDs have no enforced uniqueness check at PR time. Before adding a script, verify:
```bash
grep -r "uid: <your-new-uid>" script/ automation/
```

### 2. Undeclared `new_env_keys`

Any env key set in `postprocess` but not declared in `meta.yaml new_env_keys`
is silently dropped — it will not reach the caller. Symptoms: parent script
receives `None`/empty for a key. Fix: add the key (or a wildcard) to `new_env_keys`.

### 3. `skip_if_env` value semantics

`skip_if_env: {KEY: ['on']}` means "skip if KEY is set to any truthy value"
(not literally the string `'on'`). The engine interprets common truthy strings
(`'yes'`, `'true'`, `'1'`, `'on'`) uniformly. See `automation/script/module.py`.

### 4. ADR tag format

`add_deps_recursive` targets deps by their `names:` handle, not their tags.
A dep without `names:` cannot be overridden by ADR.

---

## Constraints

### Do not modify (generated or vendored)

| Path | Reason |
|---|---|
| `mlc-cached-state.json` (in `~/MLC/repos/local/cache/`) | Auto-generated; hand-editing breaks cache invalidation |
| `tmp-env.sh` / `tmp-env.bat` | Runtime-generated env snapshots; regenerated on every run |
| `ml-run-script-versions.json` | Auto-generated version provenance |
| `git_commit_hash.txt` | Written by build; do not edit |

### Sensitive / fragile areas

| Area | Notes |
|---|---|
| `automation/script/module.py` | 6,207-line engine; changes affect every script. Test on Linux, macOS, Windows. |
| `automation/script/cache_utils.py` | 18,555 lines; wrong change silently skips or re-runs steps |
| `automation/script/docker.py` / `apptainer.py` | Container launch + teardown; side effects outside the process |
| `automation/script/meta_schema.py` | Adding a key requires updating `lint.py`; removing silently accepts invalid YAML |
| `automation_uid: 5b4e0237da074764` | UID of the `script` automation type. All scripts share this value because the repo currently has only one automation type. Do not change. |
| `.github/workflows/` | 45 workflow files; modifying trigger paths can silence CI for entire vendor families |

### Branch policy

All changes go through a PR against the `main` branch. `dev` is kept in sync
with `main` and is only used when changes need to be merged without approval
(e.g. for urgent testing).

### API key handling

API keys are passed via `--api_key=...` → `MLC_MLPERF_ENDPOINT_API_KEY`.
They are never written to `meta.yaml`, `results.json`, or cache files.
Do not log env var values that may contain keys.

---

## Answered questions (previously open)

1. **UID generation** — use `python -c "import secrets; print(secrets.token_hex(8))"`.
   No canonical tool exists; manual generation + grep-for-collision is the standard approach.

2. **Windows `run.bat` selection** — The engine checks OS type and runs `run.bat` on Windows,
   `run.sh` on Unix. A script without `run.bat` will fail on Windows. Required for Windows CI.

3. **`predeps: bool`** — Setting `predeps: true` at the top level is a legacy flag that forces
   the deps list to be treated as pre-hook deps (run before preprocess). The modern equivalent
   is `prehook_deps:`. Prefer `prehook_deps:` in new scripts.
