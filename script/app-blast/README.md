# app-blast

Builds [BLAST+](https://github.com/ncbi/ncbi-cxx-toolkit-public) (the NCBI Basic
Local Alignment Search Tool) from the NCBI C++ Toolkit source.

## Usage

```bash
mlcr app,blast,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_BLAST_SRC_PATH` | NCBI C++ Toolkit source directory |
| `MLC_BLAST_BIN_PATH` | Directory containing the `blastn` binary (added to `PATH`) |

## Test

The `tests` block is intentionally empty: building BLAST+ from the NCBI C++
Toolkit is a very large (multi-hour) compilation that exceeds the `ubuntu-latest`
CI budget. Run the build manually on a suitable host.
