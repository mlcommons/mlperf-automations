# app-cesm

Builds [CESM](https://github.com/ESCOMP/CESM.git) — Community Earth System Model.

## Usage

```bash
mlcr app,cesm,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_CESM_SRC_PATH` | CESM source directory |
| `MLC_CESM_INSTALL_PATH` | Install prefix |
| `MLC_CESM_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
