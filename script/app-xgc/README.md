# app-xgc

Builds [XGC](https://github.com/PPPLDeepLearning/XGC-Devel.git) — a gyrokinetic particle-in-cell code for the tokamak edge.

## Usage

```bash
mlcr app,xgc,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Access-controlled and depends on PETSc/Kokkos; not publicly buildable. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
