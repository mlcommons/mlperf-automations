# app-su2

Builds [SU2](https://github.com/su2code/SU2.git) — open-source compressible CFD and adjoint solver.

## Usage

```bash
mlcr app,su2,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_SU2_SRC_PATH` | SU2 source directory |
| `MLC_SU2_INSTALL_PATH` | Install prefix |
| `MLC_SU2_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
