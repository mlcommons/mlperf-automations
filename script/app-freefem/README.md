# app-freefem

Builds [FreeFEM](https://github.com/FreeFem/FreeFem-sources.git) — a high-level PDE solver based on the finite-element method.

## Usage

```bash
mlcr app,freefem,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Downloads and builds many third-party solvers; long build. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
