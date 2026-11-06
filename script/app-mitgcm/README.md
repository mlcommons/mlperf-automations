# app-mitgcm

Builds [MITgcm](https://github.com/MITgcm/MITgcm.git) — ocean/atmosphere general-circulation model.

## Usage

```bash
mlcr app,mitgcm,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_MITGCM_SRC_PATH` | MITgcm source directory |
| `MLC_MITGCM_INSTALL_PATH` | Install prefix |
| `MLC_MITGCM_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
