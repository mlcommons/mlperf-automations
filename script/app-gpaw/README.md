# app-gpaw

Builds [GPAW](https://gitlab.com/gpaw/gpaw.git) — grid-based projector-augmented-wave DFT code.

## Usage

```bash
mlcr app,gpaw,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_GPAW_SRC_PATH` | GPAW source directory |
| `MLC_GPAW_INSTALL_PATH` | Install prefix |
| `MLC_GPAW_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
