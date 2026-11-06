# app-ansys-fluent

Builds [Ansys Fluent](https://example.com) — commercial CFD solver.

## Usage

```bash
mlcr app,ansys-fluent,hpc --src=/path/to/ansys-fluent --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_ANSYS_FLUENT_SRC_PATH` | Ansys Fluent source directory |
| `MLC_ANSYS_FLUENT_INSTALL_PATH` | Install prefix |
| `MLC_ANSYS_FLUENT_BIN_PATH` | Directory added to `PATH` |

## Test

`Ansys Fluent` is proprietary; the `tests` block is empty and the build expects a user-supplied `--src` path.
