# app-mom6

Builds [MOM6](https://github.com/mom-ocean/MOM6.git) — modular ocean model (MOM6).

## Usage

```bash
mlcr app,mom6,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_MOM6_SRC_PATH` | MOM6 source directory |
| `MLC_MOM6_INSTALL_PATH` | Install prefix |
| `MLC_MOM6_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
