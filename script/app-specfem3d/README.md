# app-specfem3d

Builds [SPECFEM3D](https://github.com/SPECFEM/specfem3d), a spectral-element
solver for 3D seismic wave propagation, from source.

## Usage

```bash
mlcr app,specfem3d,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_SPECFEM3D_SRC_PATH` | SPECFEM3D source directory |
| `MLC_SPECFEM3D_BIN_PATH` | Directory containing the `xspecfem3D` binary (added to `PATH`) |

## Test

`tests.run_inputs` configures a serial (non-MPI) build and verifies the
`xspecfem3D` solver binary is produced. Triggered in CI on `ubuntu-latest`.
