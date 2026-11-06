# app-root

Builds [ROOT](https://github.com/root-project/root.git) — the CERN data-analysis framework.

## Usage

```bash
mlcr app,root,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Very large C++ build; impractical within a 2-vCPU/6-hour CI runner. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
