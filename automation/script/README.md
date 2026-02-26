# MLC Script Automation — How It Works

This document explains what happens under the hood when you run an MLC (MLCFlow) script, from the user's first command all the way to the final output and caching.

---

## Table of Contents

1. [Overview](#overview)
2. [Running a Script](#running-a-script)
3. [Script Anatomy — What Lives Inside a Script Folder](#script-anatomy--what-lives-inside-a-script-folder)
4. [Execution Lifecycle — Step by Step](#execution-lifecycle--step-by-step)
   - [Phase 1: Input Parsing & Environment Setup](#phase-1-input-parsing--environment-setup)
   - [Phase 2: Script Discovery](#phase-2-script-discovery)
   - [Phase 3: Variation Resolution](#phase-3-variation-resolution)
   - [Phase 4: Version Resolution](#phase-4-version-resolution)
   - [Phase 5: Cache Lookup](#phase-5-cache-lookup)
   - [Phase 6: Dependency Execution](#phase-6-dependency-execution)
   - [Phase 7: Preprocessing (customize.py → preprocess)](#phase-7-preprocessing-customizepy--preprocess)
   - [Phase 8: Native Script Execution](#phase-8-native-script-execution)
   - [Phase 9: Postprocessing (customize.py → postprocess)](#phase-9-postprocessing-customizepy--postprocess)
   - [Phase 10: Post-Dependencies](#phase-10-post-dependencies)
   - [Phase 11: Caching & Finalization](#phase-11-caching--finalization)
5. [Dependency Types](#dependency-types)
6. [Environment Export Control (`new_env_keys` / `new_state_keys`)](#environment-export-control-new_env_keys--new_state_keys)
7. [Caching System](#caching-system)
8. [Variations](#variations)
9. [Variation Meta — Groups, Defaults & Combined Variations](#variation-meta--groups-defaults--combined-variations)
10. [Conditional Meta Updates (`update_meta_if_env`)](#conditional-meta-updates-update_meta_if_env)
11. [Docker Execution](#docker-execution)
12. [Experiment Mode](#experiment-mode)
13. [Key CLI Flags](#key-cli-flags)
14. [Environment Variable Conventions](#environment-variable-conventions)
15. [Glossary](#glossary)

---

## Overview

MLC Script Automation is the engine that makes native shell scripts (bash/bat) **portable, deterministic, reusable, and reproducible** across different operating systems and environments. It wraps native scripts with:

- **Automatic dependency resolution** — needed tools and models are fetched/built before a script runs.
- **Intelligent caching** — completed script outputs are cached and reused to avoid redundant work.
- **Variations** — parameterized script behaviors selectable via tags (e.g., `_cuda`, `_onnxrt`, `_fp16`).
- **Version management** — specific versions of tools, models, and libraries can be requested and enforced.
- **Docker integration** — scripts can be transparently run inside Docker containers.
- **Experiment tracking** — results can be recorded with system state snapshots for reproducibility.

---

## Running a Script

The primary user-facing command is:

```bash
# Run by tags (most common)
mlcr "detect,os"

# Run by tags with variations
mlcr "get,ml-model,_onnx,_resnet50"

# Run by script alias
mlcr detect-os

# With extra flags
mlcr "download,file" --url=https://example.com/file.tar.gz --force_cache --quiet
```

**What `mlcr` actually does:** it calls the `ScriptAutomation.run()` method in `module.py`, which orchestrates the entire lifecycle described below.

### Command Aliases & Shorthand

MLC provides several equivalent ways to invoke scripts and their modes:

| Long Form | Short Command | Alternative |
|---|---|---|
| `mlcr "tags"` | `mlc run "tags"` | Run a script |
| `mlcr "tags" --docker` | `mlcd "tags"` | `mlc docker-run "tags"` |
| `mlcr "tags" --experiment` | `mlce "tags"` | `mlc experiment "tags"` |

Examples:

```bash
# These are all equivalent — run inside Docker:
mlcr "app,mlperf,inference" --docker
mlcd "app,mlperf,inference"
mlc docker-run "app,mlperf,inference"

# These are all equivalent — run with experiment tracking:
mlcr "app,mlperf,inference" --experiment --exp_tags=v4.1
mlce "app,mlperf,inference" --exp_tags=v4.1
mlc experiment "app,mlperf,inference" --exp_tags=v4.1
```

---

## Script Anatomy — What Lives Inside a Script Folder

Each script lives in its own directory under `script/`. Here is a typical structure:

```
script/download-file/
├── meta.yaml          # Script metadata: tags, deps, variations, env keys, caching config
├── customize.py       # Python hooks: preprocess(), postprocess(), predeps(), detect_version()
├── run.sh             # Native bash script (Linux/macOS)
├── run.bat            # Native batch script (Windows)
├── run-ubuntu.sh      # OS-specific script variant (optional)
├── validate_cache.sh  # Cache validation script (optional)
├── README.md          # Documentation
└── tests/             # Test cases
```

### `meta.yaml` — The Blueprint

This is the most important file. It declares:

| Field | Purpose |
|---|---|
| `alias` | Human-friendly name (e.g., `download-file`) |
| `uid` | Unique ID for the script |
| `tags` | Searchable tags (e.g., `download`, `file`, `download-file`) |
| `deps` | Dependencies — other MLC scripts to run first |
| `post_deps` | Scripts to run after the main script |
| `prehook_deps` | Scripts to run after preprocessing but before the native script |
| `posthook_deps` | Scripts to run after the native script but before postprocessing/post_deps |
| `variations` | Named parameter sets selectable via `_tag` syntax |
| `versions` | Version-specific overrides |
| `default_env` | Default environment variables |
| `env` | Environment variables always set |
| `new_env_keys` | Keys to export to the caller after execution |
| `new_state_keys` | State keys to export to the caller |
| `cache` | Whether to cache results (`true`/`false`) |
| `can_force_cache` | Allow user to force caching with `--force_cache` |
| `cache_expiration` | Auto-expire cached entries (e.g., `1h`, `7d`) |
| `input_mapping` | Maps CLI flags to environment variables |
| `docker` | Docker-specific configuration |
| `clean_output_files` | Files to remove before running |

### `customize.py` — Python Hooks

Optional Python file with lifecycle hooks:

| Function | When Called | Purpose |
|---|---|---|
| `predeps(i)` | Before dependency resolution | Dynamically modify dependencies or environment |
| `preprocess(i)` | After deps, before native script | Prepare commands, validate inputs, set env variables |
| `postprocess(i)` | After native script runs | Parse output, detect versions, set result env variables |
| `detect_version(i)` | During cache validation | Detect the installed version of a tool |

---

## Execution Lifecycle — Step by Step

When you run `mlcr "download,file,_curl" --url=https://example.com/data.zip`, here is exactly what happens:

```
┌──────────────────────────────────────────────────────────┐
│                    User Command                          │
│  mlcr "download,file,_curl" --url=...                    │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 1: Input Parsing & Environment Setup              │
│  • Parse tags, variation tags (_curl), CLI flags         │
│  • Detect host OS (platform, flavor, arch)               │
│  • Initialize env, state, const dictionaries             │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 2: Script Discovery                               │
│  • Search for scripts matching tags: download,file       │
│  • If multiple found → interactive selection or quiet    │
│  • Load meta.yaml from selected script                   │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 3: Variation Resolution                           │
│  • Map _curl → variation "curl" in meta.yaml             │
│  • Apply variation env, deps, and defaults               │
│  • Resolve base variations, groups, combined variations  │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 4: Version Resolution                             │
│  • Check --version, --version_min, --version_max         │
│  • Apply version-specific meta overrides                 │
│  • Set MLC_VERSION, MLC_VERSION_MIN, MLC_VERSION_MAX     │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│  Phase 5: Cache Lookup                                   │
│  • If script has cache: true in meta                     │
│  • Search local cache by tags + variations + version     │
│  • Validate found entries (check paths, run              │
│    validate_cache script, check version bounds)          │
│  • If valid cache found → load env/state, skip to       │
│    post-deps and return                                  │
│  • If not found → create temporary cache entry           │
└────────────────────────┬─────────────────────────────────┘
                         │
            ┌────────────┴────────────┐
            │ Cached?                 │
     ┌──YES─┤                         ├─NO──┐
     │      └─────────────────────────┘     │
     │                                      │
     ▼                                      ▼
  Load cached                    ┌──────────────────────┐
  env & state,                   │  Phase 6: Run Deps   │
  run post_deps                  │  (see below)         │
  & return                       └──────────┬───────────┘
                                            │
                                            ▼
                                 ┌──────────────────────┐
                                 │  Phase 7: Preprocess  │
                                 └──────────┬───────────┘
                                            │
                                            ▼
                                 ┌──────────────────────┐
                                 │  Phase 8: Run Native  │
                                 │  Script (run.sh/bat)  │
                                 └──────────┬───────────┘
                                            │
                                            ▼
                                 ┌──────────────────────┐
                                 │  Phase 9: Postprocess │
                                 └──────────┬───────────┘
                                            │
                                            ▼
                                 ┌──────────────────────┐
                                 │  Phase 10: Post-Deps  │
                                 └──────────┬───────────┘
                                            │
                                            ▼
                                 ┌──────────────────────┐
                                 │  Phase 11: Cache &    │
                                 │  Finalize             │
                                 └──────────────────────┘
```

### Phase 1: Input Parsing & Environment Setup

1. Parse the command-line into tags and key-value inputs.
2. Separate **script tags** (e.g., `download`, `file`) from **variation tags** (prefixed with `_`, e.g., `_curl`).
3. Map CLI flags to environment variables via `input_mapping` (e.g., `--url` → `MLC_DOWNLOAD_URL`).
4. Detect the host OS (platform, flavor, version, architecture) and store in `os_info`.
5. Import relevant host environment variables (proxies, `HOME`, `GH_TOKEN`, etc.).
6. Initialize the global `env`, `state`, `const`, and `const_state` dictionaries.

### Phase 2: Script Discovery

1. Search all registered MLC script repositories for scripts matching the given tags.
2. If multiple scripts match, the user is prompted to select one interactively (unless `--quiet` mode).
3. Previously remembered selections are reused automatically.
4. If caching is enabled, cache entries are preloaded and used to help disambiguate scripts.
5. The selected script's `meta.yaml` is loaded and becomes the blueprint for execution.

### Phase 3: Variation Resolution

Variations customize a script's behavior without needing separate scripts.

1. Variation tags from the command (e.g., `_curl`) are matched against the `variations` section in `meta.yaml`.
2. **Groups**: Variations can belong to groups (e.g., `download-tool`). Only one variation per group is active.
3. **Defaults**: If no variation from a group is selected, the `default: true` variation is used.
4. **Base variations**: A variation can declare base dependencies on other variations.
5. **Combined variations**: Comma-separated keys (e.g., `"cuda,fp16"`) activate when all component variations are present.
6. **Dynamic variations**: Pattern-based tags like `url.#` match `_url.https://...` and substitute the dynamic value.
7. Each active variation's `env`, `deps`, `default_env`, and other meta fields are merged into the script's configuration.

### Phase 4: Version Resolution

Version resolution follows a priority chain:

1. **CLI input** (`--version=3.10`) — highest priority
2. **Environment variable** (`MLC_VERSION=3.10`)
3. **Script meta** (`version: 3.10` in `meta.yaml`)
4. **Default version** (`default_version` in meta) — lowest priority

Version constraints (`version_min`, `version_max`, `version_max_usable`) are enforced. If a specific version has a `versions` entry in `meta.yaml`, additional version-specific overrides (env, deps, ADR) are applied.

### Phase 5: Cache Lookup

If the script has `cache: true` in its meta:

1. **Prepare cache tags** — combine script tags, variation tags, version tags, and extra cache tags.
2. **Search local cache** — look for existing cache entries matching these tags.
3. **Validate cache entries**:
   - Check that dependent paths still exist.
   - Run `validate_cache.sh/bat` if present in the script folder.
   - Verify the cached version is within requested version bounds.
   - Check cache expiration.
4. **If a valid cached entry is found**:
   - Load the saved `new_env` and `new_state` from the cache.
   - Fix any stale paths (cache directory may have moved).
   - Run any `post_deps` and return — skipping the full script execution.
5. **If not found**: Create a temporary cache entry (tagged with `tmp`), change working directory to the cache path, and proceed with full execution.

### Phase 6: Dependency Execution

Dependencies (`deps` in `meta.yaml`) are other MLC scripts that must complete before this script runs.

1. Each dependency is itself a full MLC script invocation — the process is **recursive**.
2. `predeps()` in `customize.py` is called first, allowing dynamic modification of the dependency list.
3. Dependencies can be conditional based on environment variables (`enable_if_env`, `skip_if_env`).
4. Environment variables from completed dependencies flow into the current script's environment.
5. Local env keys (like `MLC_VERSION`) are temporarily removed before running deps to avoid contamination, then restored afterward.
6. The `add_deps_recursive` (ADR) mechanism allows parent scripts to override tags/env of deeply nested dependencies.

### Phase 7: Preprocessing (`customize.py` → `preprocess`)

If `customize.py` exists and has a `preprocess()` function:

1. It receives the full environment, state, meta, and OS info.
2. It can:
   - Modify environment variables (e.g., construct download commands).
   - Build platform-specific command lines.
   - Set `skip: True` to skip this script entirely.
   - Return `script: {...}` to redirect execution to a different script.
   - Add extra cache tags dynamically.
   - Return a detected version for cache tagging.
3. After preprocessing, **prehook dependencies** (`prehook_deps`) are run.

### Phase 8: Native Script Execution

This is where the actual work happens:

1. The appropriate script file is selected based on the OS (see fallback table below).
2. A **temporary wrapper script** (`tmp-run.sh/bat`) is generated that:
   - Sets up all environment variables (from env dict → `export` statements).
   - Includes any script prefixes from state.
   - Calls the actual script file.
3. The wrapper is executed via `os.system()`.
4. The return code is checked — non-zero means failure (reported with a link to file issues).
5. If the script writes to `tmp-run-env.out`, those environment updates are loaded back.
6. If the script writes to `tmp-run-state.json`, those state updates are loaded back.

#### Platform-Specific Script Selection with Automatic Fallback

On Linux/macOS, MLC does **not** simply run `run.sh`. It uses the detected host OS information to find the **most specific script** available, falling back to more general ones. The search order is:

| Priority | Script Pattern | Example |
|---|---|---|
| 1 | `run-{flavor}-{version}-{platform}.sh` | `run-ubuntu-22.04-x86_64.sh` |
| 2 | `run-{flavor}-{version}.sh` | `run-ubuntu-22.04.sh` |
| 3 | `run-{flavor}-{platform}.sh` | `run-ubuntu-x86_64.sh` |
| 4 | `run-{flavor}.sh` | `run-ubuntu.sh` |
| 5 | `run-{flavor_like}-{platform}.sh` | `run-debian-x86_64.sh` |
| 6 | `run-{flavor_like}.sh` | `run-debian.sh` |
| 7 | `run-{os_type}-{platform}.sh` | `run-linux-x86_64.sh` |
| 8 | `run-{os_type}.sh` | `run-linux.sh` |
| 9 | `run-{platform}.sh` | `run-x86_64.sh` |
| 10 | `run.sh` | `run.sh` (default fallback) |

The environment variables used are:
- `MLC_HOST_OS_FLAVOR` — e.g., `ubuntu`, `rhel`, `arch`
- `MLC_HOST_OS_VERSION` — e.g., `22.04`, `9.3`
- `MLC_HOST_OS_FLAVOR_LIKE` — e.g., `debian` (for Ubuntu), `fedora` (for RHEL)
- `MLC_HOST_OS_TYPE` — e.g., `linux`, `darwin`
- `MLC_HOST_PLATFORM_FLAVOR` — e.g., `x86_64`, `aarch64`

This fallback only triggers if the script folder contains **at least one** prefixed script (e.g., `run-ubuntu.sh`). If only `run.sh` exists, it is used directly.

On **Windows**, the script is always `run.bat`.

### Phase 9: Postprocessing (`customize.py` → `postprocess`)

If `customize.py` exists and has a `postprocess()` function:

1. It receives the updated environment and state after the native script ran.
2. Typical uses:
   - Parse output files to extract versions, paths, or results.
   - Set final environment variables (e.g., `MLC_DOWNLOAD_DOWNLOADED_PATH`).
   - Validate the script completed successfully.
   - Add extra cache tags based on results.

### Phase 10: Post-Dependencies

1. **Posthook dependencies** (`posthook_deps`) run after the native script and postprocess.
2. **Post-dependencies** (`post_deps`) run last, after everything else.
3. These follow the same recursive execution model as regular dependencies.

### Phase 11: Caching & Finalization

1. **Save to cache**: If caching is enabled and the script succeeded:
   - `new_env` and `new_state` (the delta from this script) are saved to `mlc-cached-state.json` in the cache directory.
   - The environment export script is saved (`tmp-env.sh/bat`).
   - The `tmp` tag is removed from the cache entry, finalizing it.
   - Version and associated script metadata are recorded in the cache entry.
2. **Compute new_env/new_state**: The difference between the initial env/state and the final env/state is calculated. Only keys listed in `new_env_keys` and `new_state_keys` (from meta) are exported.
3. **Restore environment**: The original caller's environment is restored, with only the declared new keys merged in.
4. **Report timing**: If `--time` is specified, execution time is printed.
5. **Report disk usage**: If `--space` is specified, disk space used is reported.
6. **Print final info**: Keys listed in `print_env_at_the_end` (from meta) are displayed.
7. **Return**: The result dict with `env`, `new_env`, `state`, `new_state`, and `deps` is returned to the caller.

---

## Dependency Types

| Type | When | Purpose |
|---|---|---|
| `deps` | Before preprocessing | Core prerequisites (e.g., detect OS, get Python) |
| `prehook_deps` | After preprocessing, before native script | Setup that needs preprocessed env |
| `posthook_deps` | After native script, before postprocessing post-deps | Actions that need script output |
| `post_deps` | After everything | Cleanup, extraction, follow-up actions |
| Docker `deps` | Docker-specific setup | Install tools needed inside the container |
| Docker `build_deps` | Dockerfile generation | Scripts needed to build the Docker image |

### Dependency Modifiers

Dependencies support conditional execution:

```yaml
deps:
  - tags: get,generic-sys-util,_md5sha1sum
    enable_if_env:                    # Only run if these env conditions are met
      MLC_DOWNLOAD_CHECKSUM:
        - 'on'
    skip_if_env:                      # Skip if these env conditions are met
      MLC_SKIP_SYS_UTILS:
        - 'yes'
    force_env_keys:                   # Force these keys into the dep's env
      - MLC_DOWNLOAD_*
    dynamic: true                     # Always re-evaluate, even from cache
```

### Add Deps (`ad`) vs Add Deps Recursive (`adr`)

Both `ad` (alias for `add_deps`) and `adr` (alias for `add_deps_recursive`) let you customize named dependencies by overriding their `tags`, `version`, `env`, etc. The critical difference is **scope**:

| Mechanism | Scope | Safety |
|---|---|---|
| `ad` / `add_deps` | Only searches the **direct** deps/post_deps/prehook_deps/posthook_deps of the **current script** | **Safe** — changes are local |
| `adr` / `add_deps_recursive` | Searches for the named dependency **anywhere in the entire workflow tree** (all nested child scripts) | **Dangerous** — can have unintended side effects |

#### `ad` (add_deps) — Preferred

Use `ad` to override a dependency that belongs to **this script**:

```yaml
# In meta.yaml
ad:
  python:
    version_min: "3.9"
  openssl:
    tags: get,openssl,_shared
```

`ad` matches by dependency **name** (the `names` field in the dependency definition). If the named dependency is not found among the current script's deps, it is silently ignored (no error unless `fail_error` is set).

#### `adr` (add_deps_recursive) — Use with Caution

`adr` propagates the override to **every** script in the workflow. It is carried as part of `self.add_deps_recursive` and applied to deps at every level of recursion:

```bash
# From CLI — force Python 3.11 everywhere in the workflow
mlcr "app,mlperf,inference" --adr.python.version=3.11

# From CLI — force a specific compiler across the entire dependency tree
mlcr "app,mlperf,inference" --adr.compiler.tags=get,gcc --adr.compiler.version=12
```

```yaml
# In meta.yaml — USE SPARINGLY
adr:
  python:
    version_min: "3.9"
```

> **Best Practice:** Always prefer `ad` over `adr` in `meta.yaml`. Using `adr` inside a script's meta can unintentionally change dependency versions or tags in deeply nested scripts that the author did not anticipate. Reserve `adr` for **CLI overrides** where the user explicitly intends a global effect.

---

## Environment Export Control (`new_env_keys` / `new_state_keys`)

When a script finishes, MLC does **not** export its entire environment back to the parent. Instead, it computes a **diff** and exports only the keys listed in `new_env_keys` (and `new_state_keys` for state). This is critical for preventing **environment corruption** in the parent script.

```yaml
# In meta.yaml
new_env_keys:
  - MLC_DOWNLOAD_DOWNLOADED_PATH
  - MLC_DOWNLOAD_DOWNLOADED_CHECKSUM
  - MLC_DOWNLOAD_CMD

new_state_keys:
  - download
```

#### How It Works

1. Before the script runs, MLC snapshots `saved_env` and `saved_state`.
2. The script (and its dependencies) may set many environment variables.
3. After the script finishes, MLC calls `detect_state_diff()` which only keeps env keys that match entries in `new_env_keys`.
4. The original caller's environment is **restored** from the snapshot, and only the declared new keys are merged in.

#### Pattern Matching

`new_env_keys` supports **wildcard** patterns:

```yaml
new_env_keys:
  - MLC_LLVM_*             # Exports all keys starting with MLC_LLVM_
  - MLC_DATASET_?_PATH     # Single-character wildcard
  - <<<MLC_SOME_KEY>>>     # Dynamic: looks up env[MLC_SOME_KEY] and exports the key whose name equals that value
```

> **Why this matters:** Without `new_env_keys`, a child script that sets `MLC_PYTHON_BIN_PATH` internally could overwrite the parent's Python path. By declaring exactly which keys are exported, each script **isolates** its side effects.

---

## Caching System

### How It Works

- Cached outputs live in `$HOME/MLC/repos/local/cache/<uid>/`.
- Each cache entry stores:
  - `mlc-cached-state.json` — the `new_env` and `new_state` delta.
  - `tmp-env.sh` — environment export script.
  - All output files generated by the script.
  - Meta with tags, version, associated script UID, and expiration info.

### Cache Tags

Cache entries are indexed by tags like:
```
detect,os,detect-os,version-22.04,_ubuntu
```

### Cache Lifecycle

| Action | CLI Flag | Behavior |
|---|---|---|
| Normal | (none) | Search cache → reuse if found |
| Skip cache | `--skip_cache` | Don't cache and run in current directory |
| Force cache | `--force_cache` | Cache even if `can_force_cache` normally wouldn't |
| New entry | `--new` | Ignore existing cache, create a fresh entry |
| Renew | `--renew` | Rewrite existing cache entry |
| Validate | (automatic) | `validate_cache.sh` is run to verify cached entry is still valid |
| Expiration | (automatic) | Cache entries with `cache_expiration` auto-expire |

### Dependent Cached Paths (Cache Invalidation)

A script can declare that its cached output **depends on an external path**. If that path no longer exists, the cache entry is silently skipped during lookup and the script re-runs.

To use this, set `MLC_GET_DEPENDENT_CACHED_PATH` in the environment (typically in `postprocess` of `customize.py`):

```python
# In customize.py postprocess
def postprocess(i):
    env = i['env']
    # Mark cache as dependent on this external directory
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env.get('MLC_SOME_INSTALLED_PATH', '')
    return {'return': 0}
```

When MLC finalizes the cache entry, it records the path in `cached_meta['dependent_cached_path']`. On subsequent lookups, `validate_dependent_paths()` in `cache_utils.py` checks:

1. Does the `dependent_cached_path` still exist on disk?
2. If not, the cached entry is **silently skipped** and MLC proceeds as if no cache existed (triggering a fresh run).

This is useful for scripts that install or download artifacts to a location outside the cache directory — if that location is cleaned up, the cache entry becomes invalid automatically.

---

## Variations

Variations are named parameter sets that modify a script's behavior.

### Syntax

Variation tags are prefixed with `_` in the command line:

```bash
mlcr "download,file,_curl"        # Select the "curl" download tool variant
mlcr "get,ml-model,_onnx,_fp16"   # Combine multiple variations
mlcr "get,compiler,_-llvm"        # Exclude the "llvm" variation with -_ prefix
```

### Variation Features

| Feature | Description |
|---|---|
| **Groups** | Mutually exclusive variations (e.g., only one `download-tool` at a time) |
| **Defaults** | `default: true` in a group selects it when none is explicitly chosen |
| **Base** | A variation can declare dependencies on other variations |
| **Combined** | Comma-separated keys (e.g., `"cuda,fp16"`) activate for specific combos |
| **Dynamic** | Patterns like `url.#` match `_url.VALUE` and substitute `#` with `VALUE` |
| **Aliases** | One variation name can alias to another |
| **Exclusion** | Prefix with `-` or `~` to explicitly exclude a variation |

### Example (from `download-file/meta.yaml`):

```yaml
variations:
  curl:
    env:
      MLC_DOWNLOAD_TOOL: curl
    group: download-tool
  wget:
    env:
      MLC_DOWNLOAD_TOOL: wget
    group: download-tool
  mlcutil:
    default: true
    env:
      MLC_DOWNLOAD_TOOL: mlcutil
    group: download-tool
  url.#:
    env:
      MLC_DOWNLOAD_URL: '#'    # '#' is replaced with the actual value
```

---

## Variation Meta — Groups, Defaults & Combined Variations

Beyond simple key-value pairs, the `variations` dictionary in `meta.yaml` supports advanced structuring through **groups**, **defaults**, and **combined variations**.

### Variation Groups

A **group** declares a set of mutually exclusive variations. Only **one** variation from a group can be active at a time.

```yaml
variations:
  onnx:
    group: framework
    env:
      MLC_ML_FRAMEWORK: onnxruntime
  pytorch:
    group: framework
    default: true          # Selected automatically if no framework variation is specified
    env:
      MLC_ML_FRAMEWORK: pytorch
  tensorflow:
    group: framework
    env:
      MLC_ML_FRAMEWORK: tensorflow
```

Rules:
- If the user specifies no variation from a group, the one marked `default: true` is selected automatically.
- If the user specifies more than one variation from the same group, MLC reports an error.
- A variation **cannot** have both `group` and `alias` at the same time.
- A variation **cannot** have both `default` and `alias` set as top-level keys.

### `default_variations`

A variation (or combined variation) can declare `default_variations` — a dictionary mapping **group names** to **default variation tags** that should be auto-selected when the parent variation is active.

```yaml
variations:
  amd:
    env:
      MLC_TMP_ML_MODEL_PROVIDER: amd
    group: model-provider
    default_variations:
      framework: pytorch     # When "amd" is selected, auto-select "pytorch" from the "framework" group
      precision: fp8         # ... and "fp8" from the "precision" group

  70b:
    group: model-size
    default: true
    default_variations:
      huggingface-stub: meta-llama/Llama-2-70b-chat-hf

  7b:
    group: model-size
    default_variations:
      huggingface-stub: meta-llama/Llama-2-7b-chat-hf
```

A default variation from `default_variations` is applied **only if**:
1. No other variation from that target group is already selected by the user.
2. The default variation is not excluded with a `-` prefix.

### Combined Variations

Combined variations use comma-separated keys to activate **only when multiple specific variations are all active**:

```yaml
variations:
  cuda:
    group: backend
    env:
      MLC_BACKEND: cuda
  fp16:
    group: precision
    env:
      MLC_PRECISION: fp16
  "cuda,fp16":               # Only activates when BOTH cuda AND fp16 are selected
    env:
      MLC_CUDA_FP16_MODE: native
    default_env:
      MLC_CUDA_STREAMS: "2"
```

Combined variations are sorted by the number of constituent tags (fewer commas first), so broader combinations are processed before more specific ones. They can also carry their own `default_variations`, `env`, `deps`, and other meta fields.

---

## Conditional Meta Updates (`update_meta_if_env`)

`update_meta_if_env` is a powerful feature that allows a script's metadata to be **dynamically modified at runtime** based on the current environment. It is defined as a list of conditional blocks in `meta.yaml` (at the top level or inside a variation).

Each block specifies a condition and the meta fields to merge when that condition is met:

```yaml
update_meta_if_env:
  - enable_if_env:
      MLC_HOST_OS_FLAVOR:
        - ubuntu
    env:
      MLC_EXTRA_FLAG: "--ubuntu-specific"
    deps:
      - tags: get,ubuntu-tools

  - enable_if_env:
      MLC_HOST_OS_FLAVOR:
        - macos
    env:
      MLC_GENERIC_SYS_UTIL_IGNORE_VERSION_DETECTION_FAILURE: "yes"

  - skip_if_env:
      MLC_HOST_PLATFORM_FLAVOR:
        - x86_64
    docker:
      base_image: "nvcr.io/.../aarch64-ubuntu22.04-public"
```

### Condition Types

| Condition | Behavior |
|---|---|
| `enable_if_env` | Block is applied **only if** all listed env vars match one of the allowed values |
| `skip_if_env` | Block is **skipped** if any listed env var matches one of the listed values |
| `enable_if_any_env` | Block is applied if **any** of the listed env vars match |
| `skip_if_any_env` | Block is skipped if **any** of the listed env vars match |

### Mergeable Fields

When a condition matches, the following fields from the block are merged into the script's runtime metadata:

| Field | Effect |
|---|---|
| `env` | Merged into the script's environment |
| `default_env` | Merged into defaults (only sets keys not already present) |
| `const` | Merged into constants (always overwrite) |
| `state` / `const_state` | Merged into state dictionaries |
| `docker` | Merged into Docker configuration in `run_state` |
| `ad` / `add_deps` | Merged into additional dependency overrides |
| `adr` / `add_deps_recursive` | Merged into recursive dependency overrides |

### Processing Order

`update_meta_if_env` blocks are accumulated across the dependency chain — parent scripts' conditional blocks are inherited by child scripts via `run_state`. They are re-evaluated each time `update_state_from_meta()` is called (during variation merging and dependency processing), allowing conditions set by earlier scripts to affect later ones.

---

## Docker Execution

Scripts can be executed inside Docker containers for isolation and reproducibility:

```bash
# Generate Dockerfile for a script
mlcr "download,file" --docker

# Run a script inside Docker
mlcr "download,file" --docker_run

# Customize the Docker execution
mlcr "app,mlperf,inference" --docker_run --docker_image_repo=myrepo --docker_rebuild
```

### Docker Workflow

1. **Dockerfile Generation**: Uses the `build,dockerfile` MLC script to create a Dockerfile based on the target script's `docker` settings in `meta.yaml`.
2. **Dependency Resolution**: Docker-specific `build_deps` are resolved first.
3. **Mount Handling**: Host directories are automatically mounted into the container based on environment variable paths.
4. **Environment Passing**: Host env variables (proxies, tokens, etc.) are passed into the container.
5. **Execution**: The MLC run command is re-executed inside the container with `--docker_run_deps` to handle Docker-specific dependency installation.

### Docker Meta Configuration

```yaml
docker:
  run: true                    # Enable Docker execution
  real_run: true               # Execute the actual script (vs. fake run)
  deps: [...]                  # Dependencies to install inside Docker
  build_deps: [...]             # Dependencies for building the Docker image
  default_env: {...}           # Default env for Docker execution
  input_mapping: {...}         # Map CLI flags for Docker context
  pass_docker_to_script: false # Pass --docker flag to the script itself
```

---

## Experiment Mode

Experiment mode tracks script runs for reproducibility:

```bash
mlcr "app,mlperf,inference" --experiment --exp_tags=v4.1,resnet50

# Sweep over parameters
mlcr "benchmark,program" --experiment --exp.batch_size=1,2,4,8
```

### What Happens

1. An experiment entry is created/updated in `$HOME/MLC/repos/local/experiment/`.
2. A timestamped run folder is created (e.g., `run_2026-02-26_14-30-00/`).
3. **Before** the script runs: system state is captured (`system_state_before.json`).
4. The script executes normally.
5. **After** the script runs: system state is captured again (`system_state_after.json`).
6. Execution time is recorded and reported.
7. For parameter sweeps, the script is re-run for each parameter value.

---

## Key CLI Flags

| Flag | Description |
|---|---|
| `--tags` | Comma-separated tags to find a script |
| `--version` | Request a specific version |
| `--version_min` / `--version_max` | Version bounds |
| `--env.KEY=VALUE` | Set environment variable |
| `--adr.NAME.tags=TAGS` | Override a named dependency's tags recursively |
| `--quiet` / `-q` | Non-interactive mode (auto-select defaults) |
| `--verbose` / `-v` | Print detailed execution info |
| `--silent` / `-s` | Suppress most output |
| `--new` | Force a new cache entry |
| `--renew` | Renew an existing cache entry |
| `--skip_cache` | Don't use caching |
| `--force_cache` | Force caching for scripts with `can_force_cache` |
| `--fake_run` / `--prepare` | Run deps but skip the main script |
| `--fake_deps` | Fake-run all dependencies |
| `--print_deps` | Print the dependency tree |
| `--print_readme` | Generate a README with all steps |
| `--time` | Print execution time |
| `--space` | Print disk space used |
| `--debug_script` | Launch a debug shell before the native script |
| `--shell` | Open a shell with the script's environment loaded |
| `--dirty` | Don't clean temporary files |
| `--save_env` | Save env and state to files |
| `--json` / `-j` | Print output as JSON |
| `--docker` | Generate Dockerfile |
| `--docker_run` | Run inside Docker |
| `--experiment` | Enable experiment tracking |
| `--help` | Show help for a specific script |

---

## Environment Variable Conventions

MLC scripts communicate via environment variables using a consistent naming scheme:

| Prefix | Scope | Purpose |
|---|---|---|
| `MLC_` | Global | MLC-managed script variables |
| `MLC_TMP_*` | Local to script | Temporary variables stripped after script completes |
| `MLC_VERSION*` | Version control | `MLC_VERSION`, `MLC_VERSION_MIN`, `MLC_VERSION_MAX` |
| `MLC_DETECTED_VERSION` | Post-detection | Version detected by postprocess/detect_version |
| `MLC_HOST_OS_*` | OS detection | OS type, flavor, version, architecture |
| `MLC_DOWNLOAD_*` | Download scripts | URLs, tools, paths for downloads |
| `MLC_GIT_*` | Git operations | Repository URLs, branches, commits |
| `MLC_QUIET` | UX | Suppresses interactive prompts |
| `+PATH` | Path extension | Appended to `PATH` (special `+` prefix adds to lists) |

### Key Lifecycle Variables

- `MLC_TMP_CURRENT_SCRIPT_PATH` — Path to the currently executing script folder.
- `MLC_TMP_CURRENT_SCRIPT_WORK_PATH` — Working directory for the script.
- `MLC_TMP_PIP_VERSION_STRING` — Assembled pip version constraint (e.g., `>=3.10,<=3.12`).
- `MLC_EXTRA_CACHE_TAGS` — Additional tags added to cache entries.
- `MLC_RUN_STATE_DOCKER` — Whether execution is inside a Docker container.

---

## Glossary

| Term | Definition |
|---|---|
| **Script** | An MLC automation unit: a directory with `meta.yaml`, optional `customize.py`, and native scripts |
| **Tags** | Searchable labels used to find scripts (e.g., `download`, `file`) |
| **Variation** | A named parameter set that modifies script behavior (prefixed with `_`) |
| **Dependency (dep)** | Another MLC script that must run before the current one |
| **ADR** | Add Deps Recursive — mechanism to override dependency configs from parent scripts |
| **Cache** | Local storage of script outputs for reuse (`$HOME/MLC/repos/local/cache/`) |
| **Preprocess** | Python hook that runs before the native script |
| **Postprocess** | Python hook that runs after the native script |
| **Native Script** | The actual `run.sh`/`run.bat` that does the real work |
| **Meta** | The `meta.yaml` configuration file declaring a script's contract |
| **env** | The global environment dictionary passed through the script chain |
| **state** | The global state dictionary (for complex data beyond simple strings) |
| **const** | Constant env values that survive the entire script chain without being overwritten |
| **new_env** | The environment delta produced by a script (only declared keys are exported) |
| **Run State** | Internal tracking state for the current execution (deps, docker, version info) |

---

## File Reference

| File | Purpose |
|---|---|
| [`module.py`](module.py) | Core `ScriptAutomation` class — orchestrates the entire execution lifecycle |
| [`script_utils.py`](script_utils.py) | Script discovery, selection, tag parsing, `customize.py` loading |
| [`cache_utils.py`](cache_utils.py) | Cache search, validation, tag preparation, path fixing |
| [`docker.py`](docker.py) | Docker execution and Dockerfile generation logic |
| [`docker_utils.py`](docker_utils.py) | Docker-specific utilities (mounts, env, command generation) |
| [`experiment.py`](experiment.py) | Experiment mode — parameter sweeps and result tracking |
| [`help.py`](help.py) | Script help display — shows inputs, variations, and file paths |
| [`doc.py`](doc.py) | Documentation generation for scripts |
| [`lint.py`](lint.py) | Script linting and validation |
| [`remote_run.py`](remote_run.py) | Remote execution support |
| [`meta.json`](meta.json) | Automation-level metadata for the "script" automation type |
