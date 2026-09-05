"""Merge per-node infragraph topologies into one multi-node Infrastructure.

Each node contributes a single-node `dev.yaml` produced by
`infragraph translate lstopo`, which has the shape:

    devices:   [ {name: <device>, components: [...], links: [...], edges: [...]} ]
    instances: [ {name: <device>, device: <device>, count: 1} ]

The merge:

  * unions the `devices` arrays, deduplicating devices that are structurally
    identical (the common homogeneous-cluster case, so N nodes of the same
    model yield one device definition rather than N copies);
  * emits one `instances` entry per node, named after that node's real
    hostname (read from its lstopo XML), so that generated graph node names
    carry the node identity -- `spark-3d96.0.cpu.0` -- and each node can be
    annotated with its own sysinfo;
  * annotates each node's cpu / xpu graph nodes from that node's
    `mlperf-system-info-single-node-<id>.json`.

No infrastructure-level `edges` are emitted: lstopo sees one host only, so
there is no observable inter-node fabric to infer. The merged graph is a set
of node subgraphs, not a fabric topology.
"""

import argparse
import copy
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml
from infragraph import *
from infragraph.infragraph_service import InfraGraphService


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dir", required=True,
                   help="Directory holding the per-node dev-node-<id>.yaml and "
                        "mlperf-system-info-single-node-<id>.json files.")
    p.add_argument("--node-ids", required=True,
                   help="Comma-separated node ids to merge, in order.")
    p.add_argument("--output", required=True,
                   help="Path of the merged annotated infragraph JSON to write.")
    p.add_argument("--merged-yaml", required=True,
                   help="Path of the merged Infrastructure YAML to write.")
    p.add_argument("--name", default="multi-node-system",
                   help="Name of the merged infrastructure.")
    return p.parse_args()


def build_type_query(*node_types):
    """One attribute query carrying a named node_filter per component type."""
    request = QueryRequest()
    for node_type in node_types:
        node_filter = request.attribute_query.node_filters.add(
            name=f"{node_type} filter")
        node_filter.attribute_filters.attributes.add(
            attribute="type", value=node_type)
    return request


def matched_nodes(response, node_type):
    """Nodes matched by the `<node_type> filter`. attribute_filters matching is
    substring based, so keep only the exact `type` hits."""
    for result in response.attribute_query.nodes:
        if result.name != f"{node_type} filter":
            continue
        return [node for node in result.nodes
                if any(a.attribute == "type" and a.value == node_type
                       for a in node.attributes)]
    return []


def _unique_name(base, taken):
    """Return `base` if free, else `base-2`, `base-3`, ... ."""
    if base not in taken:
        return base
    suffix = 2
    while f"{base}-{suffix}" in taken:
        suffix += 1
    return f"{base}-{suffix}"


def _sanitize_instance_name(name):
    """Make `name` safe to use as an infragraph instance name.

    Generated graph node names are "<instance>.<idx>.<component>.<idx>" and
    infragraph recovers the instance by splitting on '.', so a dot inside the
    instance name would corrupt node addressing. An FQDN such as
    `node1.cluster.local` therefore becomes `node1-cluster-local`. Whitespace
    is collapsed for the same reason it is avoided elsewhere: these names end
    up in shell output and query filters.
    """
    cleaned = "-".join(str(name).split())
    return cleaned.replace(".", "-")


def node_display_name(dir_path, node_id):
    """The node's real hostname, read from its lstopo XML.

    lstopo records the host it ran on as a single
    `<info name="HostName" value="..."/>` element, and this script already has
    every node's XML on disk from the fan-out, so the hostname costs no extra
    remote work. Falls back to `node-<id>` when the XML is missing the element
    (lstopo omits HostName on some platforms) so naming never hard-fails.
    """
    xml_path = dir_path / f"topo-node-{node_id}.xml"
    if xml_path.exists():
        try:
            tree = ET.parse(xml_path)
            for info in tree.iter("info"):
                if info.get("name") == "HostName":
                    value = (info.get("value") or "").strip()
                    if value:
                        return _sanitize_instance_name(value)
        except ET.ParseError as e:
            print(f"[WARN] node {node_id}: could not parse {xml_path} for a "
                  f"hostname ({e}); falling back to node-{node_id}.",
                  file=sys.stderr)
            return f"node-{node_id}"
    print(f"[WARN] node {node_id}: no HostName in {xml_path}; falling back to "
          f"node-{node_id}.", file=sys.stderr)
    return f"node-{node_id}"


def merge_devices(node_ids, dir_path):
    """Build the merged Infrastructure dict and the node_id -> instance map.

    Returns (merged_dict, instance_of_node) where instance_of_node maps a node
    id to the instance name that node's components live under.
    """
    devices = {}          # device name -> device dict
    instance_of_node = {}  # node id -> instance name
    device_of_node = {}   # node id -> device name

    for node_id in node_ids:
        dev_path = dir_path / f"dev-node-{node_id}.yaml"
        if not dev_path.exists():
            print(f"[ERROR] missing per-node topology: {dev_path}",
                  file=sys.stderr)
            sys.exit(1)

        with open(dev_path, "r", encoding="utf-8") as f:
            per_node = yaml.safe_load(f) or {}

        node_devices = per_node.get("devices") or []
        if len(node_devices) != 1:
            print(f"[ERROR] {dev_path} declares {len(node_devices)} devices; "
                  "expected exactly 1 from `infragraph translate lstopo`.",
                  file=sys.stderr)
            sys.exit(1)

        device = copy.deepcopy(node_devices[0])
        original_name = device.get("name") or f"node-{node_id}"

        # Reuse an existing device definition when this node is structurally
        # identical to one already merged. Compare with the name masked out so
        # a renamed-but-identical device still dedupes.

        # This block checks whether the current node's device definition is a duplicate of one already merged, so identical hardware isn't stored twice
        reused = None
        probe = dict(device, name=None)
        for existing_name, existing in devices.items():
            if dict(existing, name=None) == probe:
                reused = existing_name
                break

        if reused is None:
            device_name = _unique_name(original_name, devices)
            device["name"] = device_name
            devices[device_name] = device
        else:
            device_name = reused

        # Instances are named after the node's real hostname rather than
        # node-<id>, so graph node ids read as `spark-3d96.0.cpu.0`. Two nodes
        # can legitimately report the same hostname (cloned images, a
        # misconfigured cluster), and duplicate instance names would silently
        # collapse two nodes into one, so uniqueness is enforced here.
        instance_name = _unique_name(
            node_display_name(dir_path, node_id),
            set(instance_of_node.values()))
        instance_of_node[node_id] = instance_name
        device_of_node[node_id] = device_name

    merged = {
        "devices": list(devices.values()),
        "instances": [
            {
                "name": instance_of_node[node_id],
                "device": device_of_node[node_id],
                "count": 1,
                # Keep the node id in the description: it is the only link back
                # to that node's mlperf-system-info-single-node-<id>.json.
                "description": f"node {node_id}",
            }
            for node_id in node_ids
        ],
    }
    return merged, instance_of_node


def load_sysinfo(dir_path, node_id):
    """Load a node's sysinfo JSON. Returns {} when it is absent."""
    path = dir_path / f"mlperf-system-info-single-node-{node_id}.json"
    if not path.exists():
        print(f"[WARN] no sysinfo for node {node_id} at {path}; that node's "
              "topology will be emitted unannotated.", file=sys.stderr)
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    args = parse_args()

    dir_path = Path(args.dir)
    node_ids = [n.strip() for n in args.node_ids.split(",") if n.strip()]
    if not node_ids:
        print("[ERROR] --node-ids is empty", file=sys.stderr)
        sys.exit(1)

    merged, instance_of_node = merge_devices(node_ids, dir_path)
    merged["name"] = args.name
    merged["description"] = (
        f"Merged infragraph topology for {len(node_ids)} node(s): "
        f"{', '.join(node_ids)}"
    )

    merged_yaml_path = Path(args.merged_yaml)
    with open(merged_yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(merged, f, sort_keys=True)
    print(f"[INFO] merged Infrastructure YAML written to {merged_yaml_path}")

    infra = Infrastructure().deserialize(merged)
    service = InfraGraphService()
    service.set_graph(infra)

    response = service.query_graph(build_type_query("cpu", "xpu"))
    cpu_matches = matched_nodes(response, "cpu")
    xpu_matches = matched_nodes(response, "xpu")

    annotation = Annotation()
    annotated = 0

    for node_id in node_ids:
        sysinfo = load_sysinfo(dir_path, node_id)
        if not sysinfo:
            continue

        # The single-node sysinfo JSON is a flat dict of prefixed keys; group
        # by prefix to recover the processor / accelerator attribute sets.
        processor_attrs = {k: v for k, v in sysinfo.items()
                           if k.startswith("host_processor")}
        accelerator_attrs = {k: v for k, v in sysinfo.items()
                             if k.startswith("accelerator")}

        # Graph node names are "<instance>.<idx>.<component>.<idx>", so the
        # instance name prefix is what scopes a match to this node.
        prefix = instance_of_node[node_id] + "."

        for match in cpu_matches:
            if not match.name.startswith(prefix):
                continue
            node = annotation.nodes.add(name=match.name)
            for key, value in processor_attrs.items():
                node.attributes.add(attribute=key, value=str(value))
            annotated += 1

        accel_model = accelerator_attrs.get("accelerator_model_name", "")
        node_xpus = [m for m in xpu_matches if m.name.startswith(prefix)]
        accel_hits = 0
        for match in node_xpus:
            if accel_model and accel_model not in match.name:
                continue
            node = annotation.nodes.add(name=match.name)
            for key, value in accelerator_attrs.items():
                node.attributes.add(attribute=key, value=str(value))
            annotated += 1
            accel_hits += 1

        # lstopo does not always surface the benchmark accelerator as an xpu
        # component -- a discrete GPU can land under pci_device while the
        # on-board BMC display controller is what gets typed xpu. Without this
        # warning the merged graph looks complete while carrying no
        # accelerator attributes for the node at all.
        if accelerator_attrs and not accel_hits:
            print(f"[WARN] node {node_id}: sysinfo reports accelerator "
                  f"'{accel_model}' but no xpu component in this node's "
                  "lstopo topology matches that name "
                  f"(xpu components seen: "
                  f"{[m.name.split('.', 2)[-1] for m in node_xpus] or 'none'})."
                  " Accelerator attributes were NOT attached for this node.",
                  file=sys.stderr)

    if annotated:
        service.annotate_graph(annotation)
    print(f"[INFO] annotated {annotated} graph node(s) across "
          f"{len(node_ids)} node(s)")

    get_graph_req = GraphRequest()
    get_graph_req.choice = get_graph_req.INFRAGRAPH
    get_graph_req.infragraph.annotations.choice = "full"
    graph_result = service.get_graph(get_graph_req)

    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(graph_result)

    print(f"[INFO] merged multi-node infragraph written to {output_path}")


if __name__ == "__main__":
    main()
