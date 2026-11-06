# app-bigdft

Builds [BigDFT](https://gitlab.com/l_sim/bigdft-suite.git) — a DFT code using a wavelet basis set (BigDFT suite).

## Usage

```bash
mlcr app,bigdft,hpc --quiet
```

## Test

The `tests` block is intentionally empty. The BigDFT suite Installer builds a long dependency chain and expects an out-of-source build directory. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
