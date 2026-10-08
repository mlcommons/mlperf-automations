# app-walberla

Builds [waLBerla](https://github.com/walberla/walberla.git) — a widely applicable lattice-Boltzmann framework.

## Usage

```bash
mlcr app,walberla,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Large C++ template build. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
