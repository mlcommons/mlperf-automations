# app-pencil-code

Builds [Pencil Code](https://github.com/pencil-code/pencil-code.git) — a high-order finite-difference MHD/turbulence simulation code.

## Usage

```bash
mlcr app,pencil-code,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_PENCIL_SRC_PATH` | Pencil Code source directory |
| `MLC_PENCIL_INSTALL_PATH` | Install prefix |
| `MLC_PENCIL_BIN_PATH` | Directory added to `PATH` |

## Test

Builds the `conv-slab` sample (`run.x`/`start.x`) with the GNU+MPI config and verifies it exists.
