# app-openmc

Builds [OpenMC](https://github.com/openmc-dev/openmc.git) — a Monte Carlo particle-transport code for neutron and photon simulations.

## Usage

```bash
mlcr app,openmc,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_OPENMC_SRC_PATH` | OpenMC source directory |
| `MLC_OPENMC_INSTALL_PATH` | Build directory |
| `MLC_OPENMC_BIN_PATH` | Directory added to `PATH` |

## Test

Builds the `openmc` executable (CMake, HDF5) and verifies it exists.
