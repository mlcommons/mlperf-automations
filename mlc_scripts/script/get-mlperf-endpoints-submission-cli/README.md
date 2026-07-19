# get-mlperf-endpoints-submission-cli

Installs the [endpoints-submission-cli](https://github.com/mlcommons/endpoints-submission-cli)
(and the bundled submission checker) into a **dedicated virtual environment**,
isolated from the MLC host Python. Cacheable.

```bash
# From PyPI (default)
mlcr get,mlperf,endpoints-submission-cli

# From a local checkout
mlcr get,mlperf,endpoints-submission-cli --submission_cli_src=/path/to/endpoints-submission-cli
```

## Inputs

| Input | Description |
|---|---|
| `--submission_cli_src` / `--src` | local checkout to install instead of the PyPI package |
| `--package` | PyPI package name (default `endpoints-submission-cli`) |

## Outputs

| Env key | Meaning |
|---|---|
| `MLC_MLPERF_ENDPOINTS_CLI_PYTHON_BIN` | python inside the CLI venv |
| `MLC_MLPERF_ENDPOINTS_CLI_BIN` | path to the `endpoints-submission-cli` executable |
| `MLC_MLPERF_ENDPOINTS_CLI_VENV_PATH` | venv directory |
| `MLC_MLPERF_ENDPOINTS_CLI_INSTALLED` | `yes` on success |
| `MLC_MLPERF_ENDPOINTS_CLI_VERSION` | installed version |

Authentication for the CLI is via the `PRISM_USER_API_TOKEN` environment variable.
