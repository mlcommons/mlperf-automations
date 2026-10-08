# app-abinit

Builds [ABINIT](https://github.com/abinit/abinit.git) — plane-wave DFT electronic-structure code.

## Usage

```bash
mlcr app,abinit,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_ABINIT_SRC_PATH` | ABINIT source directory |
| `MLC_ABINIT_INSTALL_PATH` | Install prefix |
| `MLC_ABINIT_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
