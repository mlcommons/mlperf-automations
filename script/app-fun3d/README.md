# app-fun3d

Builds [FUN3D](https://example.com) — NASA unstructured CFD solver (export-controlled).

## Usage

```bash
mlcr app,fun3d,hpc --src=/path/to/fun3d --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_FUN3D_SRC_PATH` | FUN3D source directory |
| `MLC_FUN3D_INSTALL_PATH` | Install prefix |
| `MLC_FUN3D_BIN_PATH` | Directory added to `PATH` |

## Test

`FUN3D` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
