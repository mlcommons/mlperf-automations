# app-mpas

Builds [MPAS](https://github.com/MPAS-Dev/MPAS-Model.git) — atmosphere/ocean model on unstructured Voronoi meshes.

## Usage

```bash
mlcr app,mpas,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_MPAS_SRC_PATH` | MPAS source directory |
| `MLC_MPAS_INSTALL_PATH` | Install prefix |
| `MLC_MPAS_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
