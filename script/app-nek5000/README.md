# app-nek5000

Builds [Nek5000](https://github.com/Nek5000/Nek5000), a spectral-element
computational fluid dynamics solver, from source.

## Usage

```bash
mlcr app,nek5000,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_NEK5000_SRC_PATH` | Nek5000 source directory |
| `MLC_NEK5000_BIN_PATH` | Directory containing the Nek5000 tools (added to `PATH`) |

## Test

`tests.run_inputs` builds the Nek5000 pre/post-processing tools (`genmap`,
`genbox`, `n2to3`) from the shared source and verifies `genmap` is produced.
A case-specific solver is built separately with `bin/makenek`. Triggered in CI
on `ubuntu-latest`.
