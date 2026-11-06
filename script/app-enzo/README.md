# app-enzo

Builds [Enzo](https://github.com/enzo-project/enzo-dev), an adaptive mesh
refinement code for astrophysics and cosmology, from source.

## Usage

```bash
mlcr app,enzo,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_ENZO_SRC_PATH` | Enzo source directory |
| `MLC_ENZO_BIN_PATH` | Directory containing the `enzo.exe` binary (added to `PATH`) |

## Test

`tests.run_inputs` configures the generic GNU/Linux machine target, points the
build at the system serial HDF5, applies the `-fallow-argument-mismatch` flag
needed by modern gfortran, and verifies `enzo.exe` is produced. Triggered in CI
on `ubuntu-latest`.
