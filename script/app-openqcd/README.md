# app-openqcd

Builds [openQCD](https://github.com/sunpho84/openQCD.git) — a lattice-QCD simulation program (Wilson fermions).

## Usage

```bash
mlcr app,openqcd,hpc --quiet
```

## Test

The `tests` block is intentionally empty. The canonical distribution is released as tarballs; public git mirrors vary. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
