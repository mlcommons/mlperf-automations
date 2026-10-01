# app-gadget4

Builds [GADGET-4](https://gitlab.mpcdf.mpg.de/vrs/gadget4), a massively parallel
cosmological N-body and SPH simulation code, from source using the built-in
`Generic-gcc` system type.

## Usage

```bash
mlcr app,gadget4,hpc --quiet
```

## Requirements

Builds against system MPI, GSL, HDF5 and FFTW3 (installed via the script's
dependencies). The bundled `test/Config.sh` selects a minimal tree-gravity
configuration.

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_GADGET4_SRC_PATH` | GADGET-4 source directory |
| `MLC_GADGET4_BIN_PATH` | Directory containing the `Gadget4` binary (added to `PATH`) |

## Test

The `tests` block is intentionally empty: GADGET-4 needs GSL/HDF5/FFTW/MPI system
packages and was not validated on the offline development host. Enable a real
`run_inputs` entry once the build is confirmed end-to-end in CI.
