# app-berkeleygw

Builds [BerkeleyGW](https://gitlab.com/BerkeleyGW/BerkeleyGW.git) — many-body perturbation theory (GW/BSE) code.

## Usage

```bash
mlcr app,berkeleygw,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_BERKELEYGW_SRC_PATH` | BerkeleyGW source directory |
| `MLC_BERKELEYGW_INSTALL_PATH` | Install prefix |
| `MLC_BERKELEYGW_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
