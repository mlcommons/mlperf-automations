# skill.md — Claude working guide for mlperf-automations

Compact task-oriented reference. Read AGENTS.md for full technical detail.

---

## Mental model (read this first)

```
mlcflow CLI  →  finds script by tags  →  resolves variations & deps  →
  customise.py:preprocess()  →  run.sh  →  customise.py:postprocess()  →
  caches new_env to ~/MLC/repos/local/cache/{uid}/
```

**Two repos, two roles:**
- `mlperf-automations` (this repo) = content: 377 script directories + `automation/` engine
- `mlcflow` = driver CLI: installs via pip, dynamically loads the engine above

**Three key files per script:**
- `meta.yaml` — identity, tags, deps, variations, env mapping (schema in `automation/script/meta_schema.py`)
- `customize.py` — Python hooks: `preprocess()` builds the shell command; `postprocess()` reads results
- `run.sh` — executes `eval "${MLC_MLPERF_ENDPOINT_CMD}"` and exits non-zero on failure

---

## Task playbooks

### "I need to understand what a script does"

```bash
cat script/<alias>/meta.yaml        # tags, deps, variations, input_mapping
cat script/<alias>/customize.py     # what it validates and what command it builds
cat script/<alias>/run.sh           # what actually executes
cat script/<alias>/README.md        # human summary
```

Key fields to read in meta.yaml: `tags`, `deps`, `variations`, `input_mapping`,
`new_env_keys`, `default_env`.

### "I need to add a new script"

1. Scaffold with `mlc add script`:
   ```bash
   # Basic skeleton (copies template,generic)
   mlc add script mlcommons@mlperf-automations:<alias> --tags=<tags>

   # Copy nearest existing script as the template instead
   mlc add script mlcommons@mlperf-automations:<alias> --tags=<tags> \
       --template_tags=app,mlperf,inference,reference
   ```
   This creates `script/<alias>/` with `meta.yaml`, `customize.py`, and `run.sh`.
   If multiple scripts match `--template_tags`, it prompts you to pick one.

2. Edit `meta.yaml` — update at minimum:
   - `alias`, `uid` (already generated), `tags`, `category`
   - `input_mapping` (CLI args → env vars)
   - `new_env_keys` (what this script promises to export)
   - `deps` chain
3. Edit `customize.py` — implement `preprocess(i)`:
   - Guard required env vars (return `{'return':1,'error':'...'}` if missing)
   - Build the shell command string in `env['MY_CMD']`
4. Edit `run.sh` — ensure it evals the command and exits non-zero on failure.
5. `mlc lint script --tags=<alias>` — fix key order
6. `mlct <alias>` — run built-in tests
7. PR → `main` branch

### "I need to add a variation"

Add to `meta.yaml variations:`:
```yaml
variations:
  my-variant:
    group: my-group        # omit group if stackable (free-standing)
    default: true          # omit if not the default
    env:
      MY_ENV_VAR: value
    deps:
      - tags: get,extra,dep   # extra dep only when this variation is active
```

Invoke: `mlcr <tags>,_my-variant` (underscore prefix on CLI).

### "I need to add a conditional dependency"

```yaml
deps:
  - tags: get,cuda
    enable_if_env:
      MLC_MLPERF_DEVICE: [gpu, cuda]   # only run if device is gpu or cuda
  - tags: get,rocm
    skip_if_env:
      MLC_HOST_OS_TYPE: [windows]      # skip on Windows
```

### "I need to debug a script that fails silently"

```bash
mlcr <tags> --verbose                    # full debug output
mlc find cache --tags=<failing-dep>      # check if dep is cached
mlc rm cache --tags=<failing-dep>        # clear dep cache and re-run
mlc show cache --tags=<script-tags>      # inspect cached new_env
cat ~/MLC/repos/local/cache/*/mlc-cached-state.json | python3 -m json.tool
```

Common root causes:
- Dep cached but stale → `mlc rm cache --tags=<dep-tags>`
- `new_env_keys` missing from meta.yaml → key is silently dropped at the boundary
- `preprocess` returned success but didn't set the expected env var → add assertion
- `MLC_TMP_*` var expected downstream but not in `new_env_keys` → rename it or declare it

### "I need to understand why an env var is not reaching a script"

Env propagation rules:
1. CLI `--key=val` → `input_mapping` → `env[MAPPED_VAR]`
2. `env` passes to deps unless dep has `clean_env_keys` that matches
3. Dep's `new_env_keys` is the **only** way values come back from a dep
4. `MLC_TMP_*` never cached, never passed to deps automatically
5. If a parent caches, only declared `new_env_keys` are replayed on cache hit

### "I need to run the inference benchmark locally for testing"

```bash
# Quickest smoke test — resnet50, onnxruntime, CPU, 500 samples
mlcr run-mlperf,inference,_submission,_short,_r6.0-dev \
     --model=resnet50 --implementation=mlcommons-python \
     --backend=onnxruntime --device=cpu \
     --scenario=Offline --test_query_count=500 --target_qps=1 \
     --hw_name=my_machine --quiet

# Find performance (tunes target QPS before a real run)
mlcr run-mlperf,inference,_find-performance,_short,_r6.0-dev \
     --model=resnet50 --implementation=mlcommons-python \
     --backend=onnxruntime --device=cpu \
     --scenario=Offline --hw_name=my_machine --quiet

# Accuracy-only run
mlcr run-mlperf,inference,_accuracy-only,_short,_r6.0-dev \
     --model=resnet50 --implementation=mlcommons-python \
     --backend=onnxruntime --device=cpu \
     --scenario=Offline --hw_name=my_machine --quiet

# Full submission run (both modes + compliance + checker + tar)
mlcr run-mlperf,inference,_submission,_full,_r6.0-dev \
     --model=resnet50 --implementation=mlcommons-python \
     --backend=onnxruntime --device=cpu \
     --scenario=Offline --execution_mode=valid \
     --submitter=MLCommons --hw_name=my_machine --quiet
```

### "I need to inspect or clear cache"

```bash
mlc find cache --tags=get,mlperf,endpoints  # find cache folder
mlc show cache --tags=get,mlperf,endpoints  # print new_env snapshot
mlc rm cache --tags=get,mlperf,endpoints    # delete specific cache
mlc rm cache -f                             # delete ALL caches
mlc prune cache                             # delete expired (past cache_expiration)
```

### "I need to run in Docker"

```bash
mlcd app,mlperf,inference,endpoints,_echo-server --num_samples=50
# Rebuilds image if meta.yaml docker: section changed:
mlcd app,mlperf,inference,endpoints --docker_rebuild
```

---

## Quick reference: meta.yaml field cheat-sheet

| Field | What it does |
|---|---|
| `alias` | Script directory name and lookup key |
| `uid` | 16-hex unique ID; never change after first commit |
| `automation_uid` | UID of the `script` automation type (`5b4e0237da074764`); the only automation type currently in this repo |
| `tags` | Comma-separated discovery tags; must be a superset of what callers request |
| `category` | Grouping label in docs |
| `default_env` | Env vars set before variation env (lowest priority) |
| `new_env_keys` | **Only** these keys leave the script; use `*` and `?` wildcards |
| `input_mapping` | CLI `--key` → `ENV_VAR` translation |
| `deps` | Scripts to run before `preprocess()` |
| `prehook_deps` | Scripts to run after `preprocess()`, before `run.sh` |
| `posthook_deps` | Scripts to run after `run.sh`, before `postprocess()` |
| `post_deps` | Scripts to run after `postprocess()` |
| `variations` | Named parameter sets; `group:` makes them mutually exclusive |
| `add_deps_recursive` / `adr` | Override tags/versions on named deps deep in subtree |
| `versions` | Per-version dep overrides and env |
| `cache` | Enable caching (default: false) |
| `cache_expiration` | Auto-invalidate after `1h` / `1d` / `1w` |
| `tests` | Inline test cases run by `mlct` |

---

## customize.py hook signatures

```python
def preprocess(i):  # before run.sh
def postprocess(i): # after run.sh
def predeps(i):     # before dep execution
def postdeps(i):    # after dep execution
```

All receive the same `i` dict:
```python
i['env']         # mutable env dict → set vars here
i['automation']  # ScriptAutomation instance → i['automation'].logger
i['os_info']     # dict from detect-os
i['meta']        # parsed meta.yaml
```

All must return `{'return': 0}` or `{'return': 1, 'error': 'reason'}`.

---

## Env variable naming conventions

No rigid rules — just two hard constraints and a naming guideline:

- **`MLC_` prefix** — use on all env vars set by MLC scripts so they are clearly distinguishable from the surrounding environment.
- **`MLC_TMP_*`** — reserved for transient vars: never cached, never passed to deps. Use this when a value is only needed within the current script's run.
- **`+VAR` in `new_env_keys`** — prepend to an existing env var (e.g. `+PATH`); the engine handles concatenation.

Everything else: name vars to reflect the script they come from and what they hold. Keep names reasonably short and meaningful — no other convention is enforced.

---

## Files to read first by task type

| Task | Read these first |
|---|---|
| Understand the inference benchmark | `script/run-mlperf-inference-app/meta.yaml`, `customize.py` |
| Reference for a new MLPerf benchmark (dep chain, variations, dispatch pattern) | `script/app-mlperf-inference-mlcommons-python/meta.yaml`, `script/run-mlperf-inference-app/meta.yaml` |
| Debug env propagation | `automation/script/module.py` (search: `new_env_keys`, `clean_env_keys`) |
| Debug caching | `automation/script/cache_utils.py` |
| Add a script | Nearest similar script + `automation/script/meta_schema.py` |
| Fix meta.yaml format | `automation/script/lint.py` |
| Run CI locally | `.github/workflows/test-mlc-script-features.yml` |
| Understand Docker path | `automation/script/docker.py` |

---

## Don'ts

- Don't use `print()` in `customize.py` — use `i['automation'].logger`
- Don't raise exceptions for recoverable errors — return `{'return': 1, 'error': '...'}`
- Don't edit `mlc-cached-state.json` or `tmp-env.sh` by hand
- Don't push directly to `main` — always open a PR; use `dev` only for urgent merges without approval
- Don't hard-code paths in `run.sh` — use env vars set by `preprocess`
- Don't change `automation_uid: 5b4e0237da074764` — it's the UID of the `script` automation type, not a script-specific value
- Don't commit API keys — pass via `--api_key=...` only
- Don't set `MLC_TMP_*` in `new_env_keys` (it's a transient namespace)
