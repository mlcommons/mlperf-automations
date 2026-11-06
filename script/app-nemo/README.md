# app-nemo

Builds [NEMO](https://example.com) — ocean general-circulation model (registration required).

## Usage

```bash
mlcr app,nemo,hpc --src=/path/to/nemo --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_NEMO_SRC_PATH` | NEMO source directory |
| `MLC_NEMO_INSTALL_PATH` | Install prefix |
| `MLC_NEMO_BIN_PATH` | Directory added to `PATH` |

## Test

`NEMO` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
