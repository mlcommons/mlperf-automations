# app-yambo

Builds [Yambo](https://github.com/yambo-code/yambo.git) — a many-body perturbation theory (GW/BSE) code built on DFT.

## Usage

```bash
mlcr app,yambo,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Requires the release-tarball-bundled IOTK/NetCDF archives (absent from a plain git clone). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
