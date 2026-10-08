# app-picongpu

Builds [PIConGPU](https://github.com/ComputationalRadiationPhysics/picongpu.git) — a many-GPU particle-in-cell code.

## Usage

```bash
mlcr app,picongpu,hpc --quiet
```

## Test

The `tests` block is intentionally empty. Targets GPU (CUDA/HIP) backends and is built per simulation with pic-build. A best-effort build recipe is in `run.sh`; enable a real test once validated in CI.
