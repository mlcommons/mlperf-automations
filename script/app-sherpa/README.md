# app-sherpa

Builds [Sherpa](https://gitlab.com/sherpa-team/sherpa.git) — a Monte-Carlo event generator for particle collisions.

## Usage

```bash
mlcr app,sherpa,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Long build with a heavy dependency stack. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
