# app-flash

Builds [FLASH](https://example.com) — multiphysics astrophysics code (academic registration required).

## Usage

```bash
mlcr app,flash,hpc --src=/path/to/flash --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_FLASH_SRC_PATH` | FLASH source directory |
| `MLC_FLASH_INSTALL_PATH` | Install prefix |
| `MLC_FLASH_BIN_PATH` | Directory added to `PATH` |

## Test

`FLASH` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
