# app-ls-dyna

Builds [LS-DYNA](https://example.com) — commercial explicit finite-element solver.

## Usage

```bash
mlcr app,ls-dyna,hpc --src=/path/to/ls-dyna --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_LS_DYNA_SRC_PATH` | LS-DYNA source directory |
| `MLC_LS_DYNA_INSTALL_PATH` | Install prefix |
| `MLC_LS_DYNA_BIN_PATH` | Directory added to `PATH` |

## Test

`LS-DYNA` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
