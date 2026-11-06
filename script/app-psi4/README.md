# app-psi4

Builds [Psi4](https://github.com/psi4/psi4.git) — open-source quantum chemistry package.

## Usage

```bash
mlcr app,psi4,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_PSI4_SRC_PATH` | Psi4 source directory |
| `MLC_PSI4_INSTALL_PATH` | Install prefix |
| `MLC_PSI4_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
