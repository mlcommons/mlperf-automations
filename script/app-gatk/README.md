# app-gatk

Builds [GATK](https://github.com/broadinstitute/gatk.git) — Genome Analysis Toolkit (variant calling).

## Usage

```bash
mlcr app,gatk,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_GATK_SRC_PATH` | GATK source directory |
| `MLC_GATK_INSTALL_PATH` | Install prefix |
| `MLC_GATK_BIN_PATH` | Directory added to `PATH` |

## Test

The `tests` block is intentionally empty (heavy dependency stack / long build). A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
