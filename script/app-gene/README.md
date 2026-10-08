# app-gene

Builds [GENE](https://example.com) — gyrokinetic plasma turbulence code (registration required).

## Usage

```bash
mlcr app,gene,hpc --src=/path/to/gene --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_GENE_SRC_PATH` | GENE source directory |
| `MLC_GENE_INSTALL_PATH` | Install prefix |
| `MLC_GENE_BIN_PATH` | Directory added to `PATH` |

## Test

`GENE` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
