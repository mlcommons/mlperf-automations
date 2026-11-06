# app-alphafold

Builds [AlphaFold](https://github.com/google-deepmind/alphafold.git) — protein-structure prediction (deep learning).

## Usage

```bash
mlcr app,alphafold,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_ALPHAFOLD_SRC_PATH` | AlphaFold source directory |
| `MLC_ALPHAFOLD_INSTALL_PATH` | Install prefix |
| `MLC_ALPHAFOLD_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
