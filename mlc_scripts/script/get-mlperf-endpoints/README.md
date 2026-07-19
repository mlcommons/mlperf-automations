# get-mlperf-endpoints

Installs the MLCommons [inference-endpoint](https://github.com/mlcommons/endpoints)
package into a **dedicated virtual environment**, isolated from the MLC host
Python so its pinned dependencies (transformers, pydantic, numpy, uvloop, …)
cannot collide with `mlc` itself.

This is a cacheable `get` script: the venv is created once and reused.

## Run

```bash
# Install from the default git source (github.com/mlcommons/endpoints)
mlcr get,mlperf,endpoints

# Install from a local source checkout (skips the git clone)
mlcr get,mlperf,endpoints --endpoints_src=/path/to/endpoints
```

## Dependencies

| Dependency | Purpose |
|------------|---------|
| `detect,os` | platform detection |
| `get,python3` | host Python used to create the venv |
| `get,mlperf,endpoints,src` | git checkout of the endpoints source (skipped when `--endpoints_src` is given) |

## Inputs

| Input | Description |
|-------|-------------|
| `--endpoints_src` / `--src` | path to a local inference-endpoint checkout; when set, the git clone is skipped and this path is installed |

## Outputs

| Env key | Meaning |
|---------|---------|
| `MLC_MLPERF_ENDPOINTS_PYTHON_BIN` | python interpreter inside the dedicated venv |
| `MLC_MLPERF_ENDPOINTS_VENV_PATH` | venv directory |
| `MLC_MLPERF_ENDPOINTS_INSTALLED` | `yes` on success |
| `MLC_MLPERF_ENDPOINTS_VERSION` | installed package version |
| `MLC_MLPERF_INFERENCE_ENDPOINTS_SOURCE` | source checkout that was installed |
