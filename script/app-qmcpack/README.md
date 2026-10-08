# app-qmcpack

Builds [QMCPACK](https://github.com/QMCPACK/qmcpack.git) — quantum Monte Carlo electronic-structure code.

## Usage

```bash
mlcr app,qmcpack,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_QMCPACK_SRC_PATH` | QMCPACK source directory |
| `MLC_QMCPACK_INSTALL_PATH` | Install prefix |
| `MLC_QMCPACK_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
