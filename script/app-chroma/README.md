# app-chroma

Builds [Chroma](https://github.com/JeffersonLab/chroma.git) — lattice QCD application suite.

## Usage

```bash
mlcr app,chroma,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_CHROMA_SRC_PATH` | Chroma source directory |
| `MLC_CHROMA_INSTALL_PATH` | Install prefix |
| `MLC_CHROMA_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
