# app-e3sm

Builds [E3SM](https://github.com/E3SM-Project/E3SM.git) — DOE Energy Exascale Earth System Model.

## Usage

```bash
mlcr app,e3sm,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_E3SM_SRC_PATH` | E3SM source directory |
| `MLC_E3SM_INSTALL_PATH` | Install prefix |
| `MLC_E3SM_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
