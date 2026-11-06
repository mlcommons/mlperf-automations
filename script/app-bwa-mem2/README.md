# app-bwa-mem2

Builds [bwa-mem2](https://github.com/bwa-mem2/bwa-mem2), the next-generation
FM-index-based short-read genome aligner, from source and runs a small
self-contained smoke test.

## Usage

```bash
mlcr app,bwa-mem2,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_BWA_MEM2_SRC_PATH` | bwa-mem2 source directory |
| `MLC_BWA_MEM2_BIN_PATH` | Directory containing the `bwa-mem2` binary (added to `PATH`) |

## Test

`tests.run_inputs` builds bwa-mem2, indexes the bundled `test/tiny.fa`, and aligns
it to itself to verify the binary works. Triggered in CI on `ubuntu-latest`.
