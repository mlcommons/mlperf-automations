# app-arepo

Builds [AREPO](https://gitlab.mpcdf.mpg.de/vrs/arepo.git) — a moving-mesh cosmological magnetohydrodynamics code.

## Usage

```bash
mlcr app,arepo,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Needs a problem-specific Config.sh + SYSTYPE; repo may be access-restricted. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
