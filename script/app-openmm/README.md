# app-openmm

Builds [OpenMM](https://github.com/openmm/openmm.git) — GPU-accelerated molecular dynamics toolkit.

## Usage

```bash
mlcr app,openmm,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_OPENMM_SRC_PATH` | OpenMM source directory |
| `MLC_OPENMM_INSTALL_PATH` | Install prefix |
| `MLC_OPENMM_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
