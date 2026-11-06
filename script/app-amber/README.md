# app-amber

Builds [AMBER](https://example.com) — biomolecular molecular dynamics (commercial; AmberTools is free).

## Usage

```bash
mlcr app,amber,hpc --src=/path/to/amber --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_AMBER_SRC_PATH` | AMBER source directory |
| `MLC_AMBER_INSTALL_PATH` | Install prefix |
| `MLC_AMBER_BIN_PATH` | Directory added to `PATH` |

## Test

`AMBER` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
