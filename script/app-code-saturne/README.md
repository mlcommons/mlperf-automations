# app-code-saturne

Builds [code_saturne](https://github.com/code-saturne/code_saturne.git) — general-purpose CFD solver.

## Usage

```bash
mlcr app,code-saturne,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_CODE_SATURNE_SRC_PATH` | code_saturne source directory |
| `MLC_CODE_SATURNE_INSTALL_PATH` | Install prefix |
| `MLC_CODE_SATURNE_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
