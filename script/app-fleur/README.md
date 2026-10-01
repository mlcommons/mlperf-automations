# app-fleur

Builds [FLEUR](https://iffgit.fz-juelich.de/fleur/fleur.git) — full-potential linearized augmented plane-wave DFT code.

## Usage

```bash
mlcr app,fleur,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_FLEUR_SRC_PATH` | FLEUR source directory |
| `MLC_FLEUR_INSTALL_PATH` | Install prefix |
| `MLC_FLEUR_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
