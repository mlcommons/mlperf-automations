# app-qchem

Builds [Q-Chem](https://example.com) — commercial quantum chemistry package.

## Usage

```bash
mlcr app,qchem,hpc --src=/path/to/qchem --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_QCHEM_SRC_PATH` | Q-Chem source directory |
| `MLC_QCHEM_INSTALL_PATH` | Install prefix |
| `MLC_QCHEM_BIN_PATH` | Directory added to `PATH` |

## Test

`Q-Chem` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
