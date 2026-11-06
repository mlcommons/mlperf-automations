# app-gtc

Builds [GTC](https://github.com/xichaoqiang/GTC.git) — the Gyrokinetic Toroidal Code for fusion plasma turbulence.

## Usage

```bash
mlcr app,gtc,hpc --quiet
```

## Test

The `tests` block is intentionally empty. The reference GTC is access-controlled; public mirrors may be incomplete. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
