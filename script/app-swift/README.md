# app-swift

Builds [SWIFT](https://github.com/SWIFTSIM/SWIFT.git) — SPH With Inter-dependent Fine-grained Tasking, a cosmological hydrodynamics simulation code.

## Usage

```bash
mlcr app,swift,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_SWIFT_SRC_PATH` | SWIFT source directory |
| `MLC_SWIFT_INSTALL_PATH` | Install prefix |
| `MLC_SWIFT_BIN_PATH` | Directory added to `PATH` |

## Test

Builds the serial `swift` executable (HDF5 enabled) and verifies it exists.
