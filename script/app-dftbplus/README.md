# app-dftbplus

Builds [DFTB+](https://github.com/dftbplus/dftbplus.git) — a fast density functional tight-binding (DFTB) electronic-structure package.

## Usage

```bash
mlcr app,dftbplus,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_DFTBPLUS_SRC_PATH` | DFTB+ source directory |
| `MLC_DFTBPLUS_INSTALL_PATH` | Install prefix |
| `MLC_DFTBPLUS_BIN_PATH` | Directory added to `PATH` |

## Test

Builds the serial `dftb+` executable (LAPACK/OpenBLAS) and verifies it exists.
