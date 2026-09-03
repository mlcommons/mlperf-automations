# generate-infograph

Builds an [infragraph](https://pypi.org/project/infragraph/) infrastructure
graph from a directory of per-node system-info captures, and renders an
interactive HTML view of it.

It is normally not run by hand. `get-mlperf-multi-node-system-info,_infragraph`
runs it as a `post_dep` once every node has reported in, which is the path most
people want. Running it directly is useful when you already have the captures
on disk and want to rebuild the graph — after editing a topology by hand, say,
or to re-render the visuals without re-probing the cluster.

## What it reads

The input directory is expected to hold, for each node, an hwloc topology and
the sysinfo JSON that shares its stem:

```
mlperf-system-info-single-node-0.lstopo.xml
mlperf-system-info-single-node-0.json
mlperf-system-info-single-node-1.lstopo.xml
mlperf-system-info-single-node-1.json
```

That pairing is the whole contract. The `.lstopo.xml` files come from
`get-mlperf-single-node-system-info,_lstopo`, which parks the topology beside
the JSON with a matching stem for exactly this reason. Nodes are discovered
from what is on disk rather than from a node list, so one node in gives you a
single-node graph and N nodes give you a multi-node one, through the same code
path.

A topology with no matching JSON still gets into the graph — it just carries no
processor or accelerator attributes, and a warning says so.

## What it writes

| File | Contents |
|------|----------|
| `infragraph.json` | The annotated graph: the merged `Infrastructure` plus the per-node sysinfo attached to each node's `cpu` and `xpu` components. This is the artifact to keep. |
| `infragraph.yaml` | The merged `Infrastructure` definition on its own, without annotations. |
| `dev-<stem>.yaml` | One per node: the raw `infragraph translate lstopo` output, kept as an intermediate so a bad merge can be traced back to the node that caused it. |
| `visuals/` | A self-contained HTML/JS bundle; open `visuals/index.html` in a browser. Suppressed by `_no_visualize`. |

## Usage

```bash
mlcr generate,infograph --input_dir=/tmp/sysinfo --graph_name=my-cluster
```

Rebuild the graph but skip the HTML bundle:

```bash
mlcr generate,infograph,_no_visualize --input_dir=/tmp/sysinfo
```

Write the graph somewhere other than next to the inputs:

```bash
mlcr generate,infograph \
  --input_dir=/tmp/sysinfo \
  --out_dir_path=/tmp/graph \
  --out_file_name=cluster.json
```

## Parameters

| Flag | Env var | Meaning |
|------|---------|---------|
| `--input_dir` | `MLC_INFRAGRAPH_INPUT_DIR_PATH` | Directory holding the per-node captures. Defaults to the current directory. |
| `--out_dir_path` | `MLC_INFRAGRAPH_OUT_DIR_PATH` | Where to write the graph and visuals. Defaults to the input directory. |
| `--out_file_name` | `MLC_INFRAGRAPH_FILE_NAME` | Name of the annotated graph JSON. Defaults to `infragraph.json`; the YAML takes the same stem. |
| `--graph_name` | `MLC_INFRAGRAPH_NAME` | Name recorded in the graph. Defaults to `single-node-system` or `multi-node-system` depending on how many nodes were found. |

## Variations

| Tag | Effect |
|-----|--------|
| `_no_visualize` | Skip the HTML visualizer bundle. The JSON and YAML are still produced. |

## How the merge works

Each node's topology becomes one infragraph *device*. Devices that are
structurally identical are stored once and instantiated per node, so a
homogeneous cluster yields one device definition rather than N copies of it.
Instances are named after each node's real hostname, read from the `HostName`
field lstopo records in its own XML — that is what puts node identity into
generated graph node names (`mlc2.0.cpu.0`) and lets each node be annotated
with its own sysinfo. Two nodes reporting the same hostname get suffixed
(`mlc2`, `mlc2-2`) rather than silently collapsing into one.

No infrastructure-level edges are emitted. lstopo sees one host at a time, so
there is no observable inter-node fabric to infer; the merged graph is a set of
per-node subgraphs, not a fabric topology.

## Requirements

- **Python 3.10 or newer.** infragraph 3.x uses PEP 604 annotations at import
  time, so on 3.9 it fails to import rather than failing to install. The script
  checks the interpreter MLC selected and says so up front. If MLC picks an
  older Python, pass `--adr.python.version_min=3.10` or clear the stale
  `get,python3` cache entry.
- `lstopo` is **not** needed here — the topologies were captured on the nodes
  themselves. Only the machine running the collection needs infragraph.
