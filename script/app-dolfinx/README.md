# app-dolfinx

Builds [DOLFINx](https://github.com/FEniCS/dolfinx.git) — the computational backend of the FEniCS project.

## Usage

```bash
mlcr app,dolfinx,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Requires the PETSc / Basix / UFL / FFCx stack not available as stock packages. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
