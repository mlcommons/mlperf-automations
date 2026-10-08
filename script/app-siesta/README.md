# app-siesta

Builds [SIESTA](https://gitlab.com/siesta-project/siesta.git) — linear-scaling DFT electronic-structure code.

## Usage

```bash
mlcr app,siesta,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_SIESTA_SRC_PATH` | SIESTA source directory |
| `MLC_SIESTA_INSTALL_PATH` | Install prefix |
| `MLC_SIESTA_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
