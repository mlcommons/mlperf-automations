# app-elmer

Builds [Elmer FEM](https://github.com/ElmerCSC/elmerfem.git) — an open-source multiphysical simulation software (finite element method).

## Usage

```bash
mlcr app,elmer,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_ELMER_SRC_PATH` | Elmer source directory |
| `MLC_ELMER_INSTALL_PATH` | Install prefix |
| `MLC_ELMER_BIN_PATH` | Directory added to `PATH` |

## Test

Builds the serial `ElmerSolver` executable (LAPACK/OpenBLAS) and verifies it exists.
