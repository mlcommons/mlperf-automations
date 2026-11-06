# app-openmolcas

Builds [OpenMolcas](https://gitlab.com/Molcas/OpenMolcas.git) — a multiconfigurational quantum-chemistry package.

## Usage

```bash
mlcr app,openmolcas,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Requires Global Arrays / HDF5 and a long Fortran build. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
