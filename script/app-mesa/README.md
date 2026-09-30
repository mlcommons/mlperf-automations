# app-mesa

Builds [MESA](https://github.com/MESAHub/mesa.git) — Modules for Experiments in Stellar Astrophysics — a stellar-evolution toolkit.

## Usage

```bash
mlcr app,mesa,hpc --quiet
```

## Test

The `tests` block is intentionally empty. MESA only builds with the official MESA SDK toolchain (MESASDK_ROOT), not a stock system compiler. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
