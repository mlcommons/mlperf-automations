# app-dalton

Builds [DALTON](https://gitlab.com/dalton/dalton.git) — a molecular electronic-structure program for response properties.

## Usage

```bash
mlcr app,dalton,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Heavy Fortran/MPI build with its own setup driver. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
