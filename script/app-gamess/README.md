# app-gamess

Builds [GAMESS (US)](https://example.com) — ab initio quantum chemistry (registration required).

## Usage

```bash
mlcr app,gamess,hpc --src=/path/to/gamess --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_GAMESS_SRC_PATH` | GAMESS (US) source directory |
| `MLC_GAMESS_INSTALL_PATH` | Install prefix |
| `MLC_GAMESS_BIN_PATH` | Directory added to `PATH` |

## Test

`GAMESS (US)` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
