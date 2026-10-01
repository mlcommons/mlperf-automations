# app-minimap2

Builds [minimap2](https://github.com/lh3/minimap2), a versatile pairwise aligner
for genomic and spliced nucleotide sequences, from source and runs a small
self-contained smoke test.

## Usage

```bash
mlcr app,minimap2,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_MINIMAP2_SRC_PATH` | minimap2 source directory |
| `MLC_MINIMAP2_INSTALL_PATH` | Install prefix |
| `MLC_MINIMAP2_BIN_PATH` | Directory containing the `minimap2` binary (added to `PATH`) |

## Test

`tests.run_inputs` builds minimap2 and runs a self-alignment of the bundled
`test/tiny.fa` to verify the binary works. Triggered in CI on `ubuntu-latest`.
