# app-genesis

Builds [GENESIS](https://github.com/genesis-release-r-ccs/genesis.git) — molecular dynamics and modeling for biomolecules.

## Usage

```bash
mlcr app,genesis,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_GENESIS_SRC_PATH` | GENESIS source directory |
| `MLC_GENESIS_INSTALL_PATH` | Install prefix |
| `MLC_GENESIS_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
