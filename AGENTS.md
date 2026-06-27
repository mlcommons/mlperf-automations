# AGENTS.md — mlperf-automations

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

**Evidence:** `automation/script/meta_schema.py`, `script/app-mlperf-inference-endpoints/meta.yaml`

```yaml
# ── Identity (all four required) ──────────────────────────────────────────────
alias: app-mlperf-inference-endpoints   # kebab-case; unique across repo
uid: 22926c07f46c4e31                   # 16 lowercase hex chars; unique across repo
automation_alias: script                # always "script"
automation_uid: 5b4e0237da074764        # FIXED CONSTANT — never change

# ── Discovery ─────────────────────────────────────────────────────────────────
category: MLPerf Inference
tags: [app, mlperf, inference, endpoints, endpoint, benchmark]
tags_help: "app mlperf inference endpoints"   # shown in --help

# ── Environment ───────────────────────────────────────────────────────────────
default_env:                            # applied before variation env
  MLC_MLPERF_ENDPOINT_MODE: offline
  MLC_MLPERF_ENDPOINT_API_TYPE: openai

new_env_keys:                           # ONLY these keys propagate to callers
  - MLC_MLPERF_ENDPOINT_QPS
  - MLC_MLPERF_ENDPOINT_SAMPLES_*      # wildcard: matches any suffix
  - MLC_MLPERF_ENDPOINT_LATENCY_*
  - +PATH                              # + prefix: append to existing env var

new_state_keys:                         # persistent state (not in env)
  - mlperf-inference-implementation

# ── Input mapping ─────────────────────────────────────────────────────────────
input_mapping:
  endpoints: MLC_MLPERF_ENDPOINT_URL   # --endpoints=http://... → env var
  model:     MLC_MLPERF_ENDPOINT_MODEL
  api_key:   MLC_MLPERF_ENDPOINT_API_KEY

input_description:                      # shown in mlcr --help
  model:
    desc: Model name advertised by the endpoint
    required: true                      # validated in preprocess

# ── Caching ───────────────────────────────────────────────────────────────────
cache: true                             # persist new_env to disk
can_force_cache: true                   # allow --force_cache override
cache_expiration: 1h                    # 1h | 1d | 1w; prune with mlc prune cache
clean_files:                            # delete these from cache dir after run
  - tmp-run.out
  - tmp-env.out

# ── Dependencies ─────────────────────────────────────────────────────────────
deps:                                   # run before preprocess
  - tags: detect,os
    names: [detect-os]                  # stable handle for adr overrides
  - tags: get,python3
    names: [python, python3]
    version_min: "3.9"
    version_max: "3.12.999"
  - tags: get,mlperf,endpoints
    names: [mlperf-endpoints]
    skip_if_env:                        # skip if env[KEY] in listed values
      MLC_USE_SYSTEM_PYTHON:
        - 'yes'
    enable_if_env:                      # only run if env[KEY] in listed values
      MLC_MLPERF_ENDPOINT_MODE:
        - offline
        - online
    enable_if_any_env:                  # run if ANY key matches (OR logic)
      MLC_GPU_AVAILABLE:
        - 'yes'
    force_env_keys:                     # pass these keys even if normally filtered
      - MLC_CUDA_HOME
    clean_env_keys:                     # strip these before passing to this dep
      - MLC_TMP_*
    dynamic: true                       # re-run this dep even when parent is cached

prehook_deps:                           # run AFTER preprocess, before run.sh
  - tags: setup,mlperf,env
    dynamic: true

posthook_deps:                          # run AFTER run.sh, before postprocess
  - tags: cleanup,tmp

post_deps:                              # run AFTER postprocess
  - tags: draw,graph,from-json
    enable_if_env:
      MLC_RUN_JSON_VERSION_INFO_FILE:
        - true

# ── Variations ────────────────────────────────────────────────────────────────
variations:
  offline:
    group: mode                         # mutually exclusive within group
    default: true                       # auto-selected if no mode variation given
    env:
      MLC_MLPERF_ENDPOINT_MODE: offline
    deps: []                            # extra deps activated by this variation

  online:
    group: mode
    env:
      MLC_MLPERF_ENDPOINT_MODE: online

  echo-server:                          # no group → free-standing, stackable
    env:
      MLC_MLPERF_ENDPOINT_USE_ECHO_SERVER: 'yes'

  cuda:
    group: device
    base: [gpu]                         # apply 'gpu' variation first, then this
    env:
      MLC_MLPERF_DEVICE: cuda

  # Combined variation: only active when BOTH "cuda" and "fp16" are requested
  cuda,fp16:
    env:
      MLC_CUDA_FP16: 'yes'

  # Dynamic variation: _batch_size.64 → MLC_BATCH_SIZE=64
  "batch_size.#":
    env:
      MLC_BATCH_SIZE: "#"              # # substituted with the value from the tag

# ── Recursive dep override (ADR) ──────────────────────────────────────────────
add_deps_recursive:                     # override tags on named deps inside subtree
  mlperf-endpoints:
    tags: _online
  python:
    version_max: "3.11.999"

# Shorthand alias
adr:
  mlperf-endpoints:
    tags: _online

# ── Version matrix ────────────────────────────────────────────────────────────
default_version: "1.0"
versions:
  "1.0":
    env:
      MLC_GIT_CHECKOUT: v1.0
    deps:
      - tags: get,python3
        version_min: "3.9"
  "2.0":
    env:
      MLC_GIT_CHECKOUT: v2.0
    deps:
      - tags: get,python3
        version_min: "3.11"

# ── Docker-specific ───────────────────────────────────────────────────────────
docker:
  base_image: nvcr.io/nvidia/pytorch:24.08-py3
  all_gpus: 'yes'
  system_site_packages: 'yes'
  mounts:
    - ${{MLC_DATASET_PATH}}:${{MLC_DATASET_PATH}}   # ← template substitution
  deps:
    - tags: get,nvidia-docker

# ── Built-in tests ────────────────────────────────────────────────────────────
tests:
  run_inputs:
    - variations_list: [offline, echo-server]
      env:
        MLC_MLPERF_ENDPOINT_NUM_SAMPLES: '50'
    - variations_list: [online, poisson, echo-server]
      env:
        MLC_MLPERF_ENDPOINT_TARGET_QPS: '50'
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

### Endpoint script family (reference implementations)

| Script alias | Tags | Role |
|---|---|---|
| `app-mlperf-inference-endpoints` | `app,mlperf,inference,endpoints` | Top-level benchmark runner |
| `get-mlperf-endpoints` | `get,mlperf,endpoints` | Installs package into dedicated venv |
| `get-mlperf-endpoints-src` | `get,mlperf,endpoints,src` | Clones the endpoints source repo |
| `generate-mlperf-endpoints-conf` | `generate,mlperf,endpoints-conf` | Produces benchmark YAML config |
| `generate-mlperf-endpoints-system-desc` | `generate,mlperf,endpoints,system-desc` | Generates submission system description |
| `run-mlperf-endpoints-submission` | `run,mlperf,endpoints,submission` | Packages a full submission |
| `get-mlperf-endpoints-submission-cli` | `get,mlperf,endpoints,submission-cli` | Installs submission CLI tools |

---

## Commands

**Evidence:** `pyproject.toml` (mlcflow), `.github/workflows/test-mlc-script-features.yml`

### Install

```bash
pip install mlcflow                      # installs mlcr/mlcd/mlca/mlct/mlcp/mlce/mlcrr CLI
pip install mlc-scripts                  # registers this repo's scripts as Python package
# OR (preferred for development):
mlc pull repo mlcommons@mlperf-automations --branch=dev
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
mlc pull repo mlcommons@mlperf-automations --branch=dev
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

1. **Choose alias** following naming conventions.
2. **Generate UID** — 16 lowercase hex chars. Generate with:
   ```python
   import secrets; print(secrets.token_hex(8))
   ```
   Then verify uniqueness: `grep -r "uid: <your-uid>" script/ automation/`
3. **Create `meta.yaml`** — four required keys + tags, input_mapping, default_env, new_env_keys, deps.
4. **Create `customize.py`** — at minimum `preprocess(i)` returning `{'return': 0}`.
5. **Create `run.sh`** — reads env vars, executes tool, exits non-zero on failure.
6. **Create `README.md`** — auto-published to docs by CI `document-scripts.yml`.
7. **Add tests** in `script/<alias>/tests/` using real `mlcr` CLI calls.
8. **Add CI workflow** in `.github/workflows/` gating PRs on your script.
9. **Lint**: `mlc lint script --tags=<your-alias>` before committing.

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

**Evidence:** `script/app-mlperf-inference-endpoints/customize.py`,
`script/app-mlperf-inference-endpoints/tests/test_endpoints_workflow.py`

### 1. `MLC_MLPERF_ENDPOINTS_PYTHON_BIN` not set

`get,mlperf,endpoints` sets this. If missing or failed silently, `preprocess`
returns `return 1`. Fix: ensure `get,mlperf,endpoints` dep is listed in meta.yaml
and its cache is valid. Run `mlc find cache --tags=get,mlperf,endpoints` to inspect.

### 2. echo-server: no dummy dataset found

The `_echo-server` variation falls back to
`<endpoints-src>/tests/assets/datasets/dummy_1k.jsonl`. If `get-mlperf-endpoints-src`
was not run or the source tree is incomplete, the file is absent and `preprocess`
fails. Fix: ensure `get,mlperf,endpoints,src` ran successfully; or pass `--src=<path>`
to use a local checkout.

### 3. Online mode without a load pattern / QPS

`_online,_poisson` requires `--target_qps`. `_online,_concurrency` requires
`--concurrency`. Omitting these causes `return 1` from `preprocess`.

### 4. CPU affinity on non-Linux

`_cpu-affinity` silently falls back to `--no-cpu-affinity` on macOS/Windows.
Do not rely on affinity in cross-platform tests.

### 5. Port exhaustion (echo-server back-to-back tests)

The test suite uses `ECHO_WORKERS = "2"` explicitly. Running many benchmarks in
quick succession exhausts `TIME_WAIT` ephemeral ports. Add `sleep(2)` between
echo-server test cases.

### 6. `from-config` mode: report_dir mismatch

When using `_from-config`, the YAML file's `report_dir` takes precedence over
`MLC_MLPERF_ENDPOINT_REPORT_DIR`. If they conflict, `postprocess` looks in the
wrong place for `results.json`. Ensure the YAML's `report_dir` matches or is
absent (script injects it automatically).

### 7. UID collisions

UIDs have no enforced uniqueness check at PR time. Before adding a script, verify:
```bash
grep -r "uid: <your-new-uid>" script/ automation/
```

### 8. Undeclared `new_env_keys`

Any env key set in `postprocess` but not declared in `meta.yaml new_env_keys`
is silently dropped — it will not reach the caller. Symptoms: parent script
receives `None`/empty for a key. Fix: add the key (or a wildcard) to `new_env_keys`.

### 9. `skip_if_env` value semantics

`skip_if_env: {KEY: ['on']}` means "skip if KEY is set to any truthy value"
(not literally the string `'on'`). The engine interprets common truthy strings
(`'yes'`, `'true'`, `'1'`, `'on'`) uniformly. See `automation/script/module.py`.

### 10. ADR tag format

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
| `automation_uid: 5b4e0237da074764` | Must appear verbatim in every `meta.yaml`. Do not change. |
| `.github/workflows/` | 45 workflow files; modifying trigger paths can silence CI for entire vendor families |

### Branch policy

All changes go through a PR against the `dev` branch. `main` is the release
branch. `dev` is the default branch mlcflow pulls (`branch: dev`).

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

4. **Submission validation** — `run-mlperf-endpoints-submission` packages results into the
   MLPerf submission directory structure. The validation checklist is external to this repo
   (mlcommons/submission-checker). No in-repo validation guide exists yet.
