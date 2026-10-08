# app-moose

Builds [MOOSE](https://github.com/idaholab/moose.git) — a multiphysics object-oriented simulation environment.

## Usage

```bash
mlcr app,moose,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Requires building PETSc and libMesh first; multi-hour build. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
