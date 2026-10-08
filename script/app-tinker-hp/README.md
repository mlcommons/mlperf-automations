# app-tinker-hp

Builds [Tinker-HP](https://github.com/TinkerTools/tinker-hp.git) — massively parallel polarizable molecular dynamics.

## Usage

```bash
mlcr app,tinker-hp,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_TINKER_HP_SRC_PATH` | Tinker-HP source directory |
| `MLC_TINKER_HP_INSTALL_PATH` | Install prefix |
| `MLC_TINKER_HP_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.

## Build requirements

Tinker-HP's CPU version is written for the Intel toolchain (ifort/ifx + Intel MPI + MKL). A full Intel oneAPI installation is required to build it; this exceeds the CI budget, so the `tests` block is intentionally empty. `run.sh` provides a working recipe for hosts with oneAPI installed.
