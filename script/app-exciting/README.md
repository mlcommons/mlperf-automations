# app-exciting

Builds [exciting](https://github.com/exciting/exciting.git) — a full-potential all-electron (L)APW+lo DFT code.

## Usage

```bash
mlcr app,exciting,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Ships machine make.inc templates; needs per-host configuration. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
