# app-charmm

Builds [CHARMM](https://github.com/charmm/charmm.git) — a molecular-dynamics package for biomolecular systems.

## Usage

```bash
mlcr app,charmm,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Requires an academic license; the source is not publicly clonable. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
