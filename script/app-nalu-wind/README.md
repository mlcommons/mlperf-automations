# app-nalu-wind

Builds [Nalu-Wind](https://github.com/Exawind/nalu-wind.git) — a generalized unstructured-CFD wind-energy solver (Trilinos).

## Usage

```bash
mlcr app,nalu-wind,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Requires a full Trilinos installation; multi-hour build. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
