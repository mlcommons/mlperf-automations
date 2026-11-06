# app-castep

Builds [CASTEP](https://example.com) — plane-wave DFT code (academic license required).

## Usage

```bash
mlcr app,castep,hpc --src=/path/to/castep --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_CASTEP_SRC_PATH` | CASTEP source directory |
| `MLC_CASTEP_INSTALL_PATH` | Install prefix |
| `MLC_CASTEP_BIN_PATH` | Directory added to `PATH` |

## Test

`CASTEP` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
