# app-kratos

Builds [Kratos Multiphysics](https://github.com/KratosMultiphysics/Kratos.git) — a framework for multiphysics finite-element solvers.

## Usage

```bash
mlcr app,kratos,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Very large C++/Python build. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
