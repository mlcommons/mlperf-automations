# app-madgraph

Builds [MadGraph5_aMC@NLO](https://github.com/mg5amcnlo/mg5amcnlo.git) — an automated matrix-element and event generator.

## Usage

```bash
mlcr app,madgraph,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Compiles generated process code on demand rather than a single binary. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
