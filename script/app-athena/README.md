# app-athena

Builds [Athena++](https://github.com/PrincetonUniversity/athena), a
radiation/GR-magnetohydrodynamics code for astrophysical fluid dynamics, from
source and runs a small self-contained smoke test.

## Usage

```bash
mlcr app,athena,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_ATHENA_SRC_PATH` | Athena++ source directory |
| `MLC_ATHENA_BIN_PATH` | Directory containing the `athena` binary (added to `PATH`) |

## Test

`tests.run_inputs` configures the `shock_tube` problem generator, builds Athena++,
and runs 5 cycles of the 1D Sod shock tube shipped in the repo. Triggered in CI
on `ubuntu-latest`.
