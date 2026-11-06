# app-hoomd-blue

Builds [HOOMD-blue](https://github.com/glotzerlab/hoomd-blue.git) — particle simulation toolkit for MD and hard-particle Monte Carlo.

## Usage

```bash
mlcr app,hoomd-blue,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_HOOMD_SRC_PATH` | HOOMD-blue source directory |
| `MLC_HOOMD_INSTALL_PATH` | Install prefix |
| `MLC_HOOMD_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
