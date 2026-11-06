# app-code-aster

Builds [Code_Aster](https://gitlab.com/codeaster/src.git) — a structural-mechanics and multiphysics FE solver.

## Usage

```bash
mlcr app,code-aster,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Requires a large numerical stack (MUMPS, MED, ...); complex build. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
