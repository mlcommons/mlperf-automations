# app-cantera

Builds [Cantera](https://github.com/Cantera/cantera.git) — an open-source suite for chemical kinetics, thermodynamics, and transport processes.

## Usage

```bash
mlcr app,cantera,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_CANTERA_SRC_PATH` | Cantera source directory |
| `MLC_CANTERA_INSTALL_PATH` | Build directory |
| `MLC_CANTERA_BIN_PATH` | Directory added to `PATH` |

## Test

Builds the core Cantera C++ shared library (SCons, system Eigen/SUNDIALS/yaml-cpp/fmt) and verifies it exists.
