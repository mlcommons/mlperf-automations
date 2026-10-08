# app-grid

Builds [Grid](https://github.com/paboyle/Grid.git) — a data-parallel C++ library for lattice QCD with SIMD/vectorised kernels.

## Usage

```bash
mlcr app,grid,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_GRID_SRC_PATH` | Grid source directory |
| `MLC_GRID_INSTALL_PATH` | Build directory |
| `MLC_GRID_BIN_PATH` | Directory added to `PATH` |

## Test

Builds the Grid library (`build/lib/libGrid.a`) with the generic SIMD backend and verifies it exists.
