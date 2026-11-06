# app-octopus

Builds [Octopus](https://gitlab.com/octopus-code/octopus.git) — real-space TDDFT electronic-structure code.

## Usage

```bash
mlcr app,octopus,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_OCTOPUS_SRC_PATH` | Octopus source directory |
| `MLC_OCTOPUS_INSTALL_PATH` | Install prefix |
| `MLC_OCTOPUS_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
