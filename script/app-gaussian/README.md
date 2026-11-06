# app-gaussian

Builds [Gaussian](https://example.com) — commercial ab initio electronic-structure package.

## Usage

```bash
mlcr app,gaussian,hpc --src=/path/to/gaussian --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_GAUSSIAN_SRC_PATH` | Gaussian source directory |
| `MLC_GAUSSIAN_INSTALL_PATH` | Install prefix |
| `MLC_GAUSSIAN_BIN_PATH` | Directory added to `PATH` |

## Test

`Gaussian` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
