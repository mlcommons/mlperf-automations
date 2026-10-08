# app-star

Builds [STAR](https://github.com/alexdobin/STAR.git) — Spliced Transcripts Alignment to a Reference, an ultrafast RNA-seq aligner.

## Usage

```bash
mlcr app,star,hpc --quiet
```

## Output environment variables

| Variable | Description |
|---|---|
| `MLC_STAR_SRC_PATH` | STAR source directory |
| `MLC_STAR_INSTALL_PATH` | Install prefix |
| `MLC_STAR_BIN_PATH` | Directory added to `PATH` |

## Test

Builds the `STAR` executable from `source/` and verifies it exists.
