"""Build one infrastructure graph out of a directory of per-node captures.

The directory is whatever `get-mlperf-multi-node-system-info,_infragraph`
leaves behind: for every node, an hwloc topology and the sysinfo JSON that
shares its stem.

    mlperf-system-info-single-node-0.lstopo.xml
    mlperf-system-info-single-node-0.json
    mlperf-system-info-single-node-1.lstopo.xml
    mlperf-system-info-single-node-1.json

Each topology is translated to an infragraph device definition, the
definitions are unioned into a single `Infrastructure`, and each node's cpu /
xpu graph nodes are annotated from that node's sysinfo. One node in equals a
single-node graph; N nodes in equals a multi-node graph -- the path through
this script is the same either way.

Structurally identical devices are emitted once and instantiated per node, so
a homogeneous cluster yields one device definition rather than N copies of it.
Instances are named after each node's real hostname, which is what puts the
node identity into generated graph node names (`mlc2.0.cpu.0`) and lets each
node be annotated with its own sysinfo.

No infrastructure-level `edges` are emitted: lstopo sees one host at a time, so
there is no observable inter-node fabric to infer. The merged graph is a set of
per-node subgraphs, not a fabric topology.
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
from infragraph.translators.translator_handler import run_translator
from infragraph.visualizer.visualize import run_visualizer

TOPOLOGY_SUFFIX = ".lstopo.xml"


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", required=True,
                   help="Directory holding the per-node *.lstopo.xml topologies "
                        "and their matching sysinfo JSON files.")
    p.add_argument("--output", required=True,
                   help="Path of the annotated infrastructure graph JSON to write.")
    p.add_argument("--output-yaml", required=True,
                   help="Path of the merged Infrastructure YAML to write.")
    p.add_argument("--name", default="multi-node-system",
                   help="Name of the merged infrastructure.")
    p.add_argument("--visuals-dir", default="",
                   help="Directory to write the visualizer bundle into. "
                        "Empty to skip visualization.")
    return p.parse_args()


def sort_key(stem):
    """Natural sort: trailing digits compare numerically, the rest lexically.

    Keeps node-2 ahead of node-10 in the instance list, so the graph reads
    against the same node numbering the submission uses. Mirrors _sort_key in
    customize.py -- the two must agree or the node count logged in preprocess
    describes a different set than the one merged here.
    """
    head = stem.rstrip("0123456789")
    tail = stem[len(head):]
    return (head, int(tail) if tail else -1)


def discover_nodes(input_dir):
    """[(stem, xml_path, sysinfo_path_or_None)] for every topology in the dir."""
    nodes = []
    for xml in sorted(input_dir.glob("*" + TOPOLOGY_SUFFIX)):
        stem = xml.name[:-len(TOPOLOGY_SUFFIX)]
        sysinfo = input_dir / (stem + ".json")
        nodes.append((stem, xml, sysinfo if sysinfo.is_file() else None))
    return sorted(nodes, key=lambda n: sort_key(n[0]))


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


def unique_name(base, taken):
    """Return `base` if free, else `base-2`, `base-3`, ... ."""
    if base not in taken:
        return base
    suffix = 2
    while f"{base}-{suffix}" in taken:
        suffix += 1
    return f"{base}-{suffix}"


def sanitize_instance_name(name):
    """Make `name` safe to use as an infragraph instance name.

    Generated graph node names are "<instance>.<idx>.<component>.<idx>" and
    infragraph recovers the instance by splitting on '.', so a dot inside the
    instance name would corrupt node addressing. An FQDN such as
    `node1.cluster.local` therefore becomes `node1-cluster-local`. Whitespace is
    collapsed for the same reason it is avoided elsewhere: these names end up in
    shell output and in query filters.
    """
    return "-".join(str(name).split()).replace(".", "-")


def node_display_name(xml_path, stem):
    """The node's real hostname, read from its lstopo XML.

    lstopo records the host it ran on as a single
    `<info name="HostName" value="..."/>` element, so the hostname costs no
    extra remote work -- the XML is already here. Falls back to the file stem
    when the element is missing (lstopo omits HostName on some platforms) so
    naming never hard-fails.
    """
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        print(f"[WARN] {stem}: could not parse {xml_path} for a hostname "
              f"({e}); falling back to {stem}.", file=sys.stderr)
        return sanitize_instance_name(stem)

    for info in tree.iter("info"):
        if info.get("name") == "HostName":
            value = (info.get("value") or "").strip()
            if value:
                return sanitize_instance_name(value)

    print(f"[WARN] {stem}: no HostName in {xml_path}; falling back to {stem}.",
          file=sys.stderr)
    return sanitize_instance_name(stem)


def translate_nodes(nodes, work_dir):
    """Run the lstopo translator over every node. Returns [(stem, dev_dict)]."""
    translated = []
    for stem, xml_path, _sysinfo in nodes:
        dev_path = work_dir / f"dev-{stem}.yaml"
        run_translator("lstopo", str(xml_path), str(dev_path), "yaml", None)
        if not dev_path.is_file():
            print(f"[ERROR] {stem}: `infragraph translate lstopo` produced no "
                  f"output at {dev_path}.", file=sys.stderr)
            sys.exit(1)
        with open(dev_path, "r", encoding="utf-8") as f:
            translated.append((stem, yaml.safe_load(f) or {}))
        print(f"[INFO] {stem}: topology translated to {dev_path}")
    return translated


def merge_devices(translated, display_names):
    """Build the merged Infrastructure dict and the stem -> instance map."""
    devices = {}           # device name -> device dict
    instance_of_node = {}  # stem -> instance name
    device_of_node = {}    # stem -> device name

    for stem, per_node in translated:
        node_devices = per_node.get("devices") or []
        if len(node_devices) != 1:
            print(f"[ERROR] {stem}: translated topology declares "
                  f"{len(node_devices)} devices; expected exactly 1 from "
                  "`infragraph translate lstopo`.", file=sys.stderr)
            sys.exit(1)

        device = copy.deepcopy(node_devices[0])
        original_name = device.get("name") or stem

        # Reuse an existing device definition when this node is structurally
        # identical to one already merged -- the homogeneous-cluster case.
        # Compare with the name masked out so a renamed-but-identical device
        # still dedupes.
        reused = None
        probe = dict(device, name=None)
        for existing_name, existing in devices.items():
            if dict(existing, name=None) == probe:
                reused = existing_name
                break

        if reused is None:
            device_name = unique_name(original_name, devices)
            device["name"] = device_name
            devices[device_name] = device
        else:
            device_name = reused

        # Two nodes can legitimately report the same hostname (cloned images, a
        # misconfigured cluster) and duplicate instance names would silently
        # collapse two nodes into one, so uniqueness is enforced here.
        instance_name = unique_name(
            display_names[stem], set(instance_of_node.values()))
        instance_of_node[stem] = instance_name
        device_of_node[stem] = device_name

    merged = {
        "devices": list(devices.values()),
        "instances": [
            {
                "name": instance_of_node[stem],
                "device": device_of_node[stem],
                "count": 1,
                # Keep the stem in the description: it is the only link back to
                # that node's sysinfo JSON once the instance has been renamed
                # to the hostname.
                "description": stem,
            }
            for stem, _ in translated
        ],
    }
    return merged, instance_of_node


def load_sysinfo(sysinfo_path, stem):
    """Load a node's sysinfo JSON. Returns {} when it is absent or unreadable."""
    if sysinfo_path is None:
        print(f"[WARN] {stem}: no matching sysinfo JSON; that node's topology "
              "will be emitted unannotated.", file=sys.stderr)
        return {}
    try:
        with open(sysinfo_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"[WARN] {stem}: could not read {sysinfo_path} ({e}); that "
              "node's topology will be emitted unannotated.", file=sys.stderr)
        return {}


def annotate(service, nodes, instance_of_node):
    """Attach each node's sysinfo to that node's cpu / xpu graph nodes."""
    response = service.query_graph(build_type_query("cpu", "xpu"))
    cpu_matches = matched_nodes(response, "cpu")
    xpu_matches = matched_nodes(response, "xpu")

    annotation = Annotation()
    annotated = 0

    for stem, _xml, sysinfo_path in nodes:
        sysinfo = load_sysinfo(sysinfo_path, stem)
        if not sysinfo:
            continue

        # The single-node sysinfo JSON is a flat dict of prefixed keys; group by
        # prefix to recover the processor / accelerator attribute sets.
        processor_attrs = {k: v for k, v in sysinfo.items()
                           if k.startswith("host_processor")}
        accelerator_attrs = {k: v for k, v in sysinfo.items()
                             if k.startswith("accelerator")}

        # Graph node names are "<instance>.<idx>.<component>.<idx>", so the
        # instance name prefix is what scopes a match to this node.
        prefix = instance_of_node[stem] + "."

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
        # warning the graph looks complete while carrying no accelerator
        # attributes for the node at all.
        if accelerator_attrs and not accel_hits:
            seen = [m.name.split(".", 2)[-1] for m in node_xpus] or "none"
            print(f"[WARN] {stem}: sysinfo reports accelerator "
                  f"'{accel_model}' but no xpu component in this node's "
                  f"topology matches that name (xpu components seen: {seen}). "
                  "Accelerator attributes were NOT attached for this node.",
                  file=sys.stderr)

    if annotated:
        service.annotate_graph(annotation)
    print(f"[INFO] annotated {annotated} graph node(s) across "
          f"{len(nodes)} node(s)")


def main():
    args = parse_args()

    input_dir = Path(args.input_dir)
    nodes = discover_nodes(input_dir)
    if not nodes:
        print(f"[ERROR] no *{TOPOLOGY_SUFFIX} topology files in {input_dir}",
              file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)
    merged_yaml_path = Path(args.output_yaml)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_yaml_path.parent.mkdir(parents=True, exist_ok=True)

    display_names = {stem: node_display_name(xml, stem)
                     for stem, xml, _ in nodes}

    # The per-node translations are intermediates; they are kept beside the
    # merged YAML rather than in a temp dir so a failed merge can be debugged
    # from what is left on disk.
    translated = translate_nodes(nodes, merged_yaml_path.parent)

    merged, instance_of_node = merge_devices(translated, display_names)
    merged["name"] = args.name
    merged["description"] = (
        f"Infrastructure graph for {len(nodes)} node(s): "
        + ", ".join(instance_of_node[stem] for stem, _, _ in nodes))

    with open(merged_yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(merged, f, sort_keys=True)
    print(f"[INFO] merged Infrastructure YAML written to {merged_yaml_path}")

    service = InfraGraphService()
    service.set_graph(Infrastructure().deserialize(merged))

    annotate(service, nodes, instance_of_node)

    get_graph_req = GraphRequest()
    get_graph_req.choice = get_graph_req.INFRAGRAPH
    get_graph_req.infragraph.annotations.choice = "full"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(service.get_graph(get_graph_req))
    print(f"[INFO] infrastructure graph written to {output_path}")

    if args.visuals_dir:
        print(f"[INFO] generating visualizer bundle in {args.visuals_dir}")
        run_visualizer(input_file=str(output_path), output=args.visuals_dir)


if __name__ == "__main__":
    main()
