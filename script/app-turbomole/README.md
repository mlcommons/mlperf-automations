# app-turbomole

Builds [TURBOMOLE](https://example.com) — commercial quantum chemistry package.

## Usage

```bash
mlcr app,turbomole,hpc --src=/path/to/turbomole --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_TURBOMOLE_SRC_PATH` | TURBOMOLE source directory |
| `MLC_TURBOMOLE_INSTALL_PATH` | Install prefix |
| `MLC_TURBOMOLE_BIN_PATH` | Directory added to `PATH` |

## Test

`TURBOMOLE` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
