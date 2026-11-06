# app-geant4

Builds [Geant4](https://github.com/Geant4/geant4.git) — a toolkit for simulating the passage of particles through matter.

## Usage

```bash
mlcr app,geant4,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Very large C++ build; impractical within a 2-vCPU/6-hour CI runner. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
