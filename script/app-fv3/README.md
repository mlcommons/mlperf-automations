# app-fv3

Builds [FV3](https://github.com/NOAA-GFDL/GFDL_atmos_cubed_sphere.git) — the GFDL finite-volume cubed-sphere atmospheric dynamical core.

## Usage

```bash
mlcr app,fv3,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Builds only within a host model (SHiELD/UFS) atop the FMS infrastructure. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
