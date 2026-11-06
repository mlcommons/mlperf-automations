# app-mfem

Builds [MFEM](https://github.com/mfem/mfem.git) — a lightweight, scalable C++ library for finite element methods.

## Usage

```bash
mlcr app,mfem,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_MFEM_SRC_PATH` | MFEM source directory |
| `MLC_MFEM_INSTALL_PATH` | Install prefix |
| `MLC_MFEM_BIN_PATH` | Directory added to `PATH` |

## Test

Builds the serial MFEM library (`libmfem.a`) with bundled dependencies and verifies it exists.
