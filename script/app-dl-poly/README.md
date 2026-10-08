# app-dl-poly

Builds [DL_POLY](https://gitlab.com/ccp5/dl-poly.git) — general-purpose classical molecular dynamics.

## Usage

```bash
mlcr app,dl-poly,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_DL_POLY_SRC_PATH` | DL_POLY source directory |
| `MLC_DL_POLY_INSTALL_PATH` | Install prefix |
| `MLC_DL_POLY_BIN_PATH` | Directory added to `PATH` |

## Test

`tests.run_inputs` builds DL_POLY and verifies the binary. Triggered in CI on `ubuntu-latest`.
