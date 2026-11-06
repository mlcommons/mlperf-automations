# app-pyfr

Builds [PyFR](https://github.com/PyFR/PyFR.git) — high-order flux-reconstruction CFD solver.

## Usage

```bash
mlcr app,pyfr,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_PYFR_SRC_PATH` | PyFR source directory |
| `MLC_PYFR_INSTALL_PATH` | Install prefix |
| `MLC_PYFR_BIN_PATH` | Directory added to `PATH` |

## Test

`tests.run_inputs` builds PyFR and verifies the binary. Triggered in CI on `ubuntu-latest`.
