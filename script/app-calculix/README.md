# app-calculix

Builds [CalculiX](https://example.com) — finite-element structural analysis (CrunchiX).

## Usage

```bash
mlcr app,calculix,hpc --src=/path/to/calculix --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_CALCULIX_SRC_PATH` | CalculiX source directory |
| `MLC_CALCULIX_INSTALL_PATH` | Install prefix |
| `MLC_CALCULIX_BIN_PATH` | Directory added to `PATH` |

## Test

`CalculiX` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
