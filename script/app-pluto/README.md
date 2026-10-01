# app-pluto

Builds [PLUTO](https://github.com/black-hole-group/pluto.git) — a modular Godunov-type code for astrophysical gas dynamics (HD/MHD).

## Usage

```bash
mlcr app,pluto,hpc --quiet
```

## Test

The `tests` block is intentionally empty. PLUTO is normally configured per problem via an interactive setup.py that generates the physics-module symlinks. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
