# app-ramses

Builds [RAMSES](https://github.com/ramses-organisation/ramses), an adaptive mesh
refinement code for astrophysical and cosmological simulations, from source.

## Usage

```bash
mlcr app,ramses,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_RAMSES_SRC_PATH` | RAMSES source directory |
| `MLC_RAMSES_BIN_PATH` | Directory containing the `ramses1d` binary (added to `PATH`) |

## Test

`tests.run_inputs` builds the serial 1D hydro executable (`ramses1d`) and verifies
the binary is produced. Triggered in CI on `ubuntu-latest`.
