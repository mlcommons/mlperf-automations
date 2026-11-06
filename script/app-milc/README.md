# app-milc

Builds [MILC](https://github.com/milc-qcd/milc_qcd) (MIMD Lattice Computation),
a suite of codes for lattice quantum chromodynamics, from source. This script
builds the `su3_rmd` Kogut-Susskind improved (asqtad) dynamical-fermion
application.

## Usage

```bash
mlcr app,milc,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_MILC_SRC_PATH` | MILC source directory |
| `MLC_MILC_BIN_PATH` | Directory containing the `su3_rmd` binary (added to `PATH`) |

## Test

`tests.run_inputs` builds the serial (`MPP=false`) `su3_rmd` application with the
GNU compiler and verifies the binary is produced. Triggered in CI on
`ubuntu-latest`.
