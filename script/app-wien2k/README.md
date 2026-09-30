# app-wien2k

Builds [WIEN2k](https://example.com) — full-potential LAPW DFT code (license required).

## Usage

```bash
mlcr app,wien2k,hpc --src=/path/to/wien2k --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_WIEN2K_SRC_PATH` | WIEN2k source directory |
| `MLC_WIEN2K_INSTALL_PATH` | Install prefix |
| `MLC_WIEN2K_BIN_PATH` | Directory added to `PATH` |

## Test

`WIEN2k` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
