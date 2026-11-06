# app-icon

Builds [ICON](https://example.com) — icosahedral weather/climate model (license required).

## Usage

```bash
mlcr app,icon,hpc --src=/path/to/icon --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_ICON_SRC_PATH` | ICON source directory |
| `MLC_ICON_INSTALL_PATH` | Install prefix |
| `MLC_ICON_BIN_PATH` | Directory added to `PATH` |

## Test

`ICON` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
