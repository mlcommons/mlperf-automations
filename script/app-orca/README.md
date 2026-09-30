# app-orca

Builds [ORCA](https://example.com) — ab initio/DFT package (binary distribution, registration required).

## Usage

```bash
mlcr app,orca,hpc --src=/path/to/orca --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_ORCA_SRC_PATH` | ORCA source directory |
| `MLC_ORCA_INSTALL_PATH` | Install prefix |
| `MLC_ORCA_BIN_PATH` | Directory added to `PATH` |

## Test

`ORCA` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
