# app-ww3

Builds [WaveWatch III](https://github.com/NOAA-EMC/WW3.git) — a third-generation ocean surface-wave model.

## Usage

```bash
mlcr app,ww3,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Built via its own switch/comp/link scripts with a selected physics switch. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
