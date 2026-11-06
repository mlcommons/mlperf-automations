import argparse
import json
import sys
from pathlib import Path

import yaml
from infragraph import *
from infragraph.infragraph_service import InfraGraphService


def parse_args():
    p = argparse.ArgumentParser(
        description="Annotate the single-node sysinfo JSON with the infragraph topology produced by `infragraph translate lstopo`.")
    p.add_argument("--sysinfo", required=True,
                   help="Path to the sysinfo JSON file (read-only).")
    p.add_argument("--infragraph", required=True,
                   help="Path to the infragraph dev.yaml file.")
    return p.parse_args()


def build_type_query(*node_types):
    """One attribute query carrying a named node_filter per component type."""
    request = QueryRequest()
    for node_type in node_types:
        node_filter = request.attribute_query.node_filters.add(name=f"{node_type} filter")
        node_filter.attribute_filters.attributes.add(attribute="type", value=node_type)
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


def main():
    args = parse_args()

    sysinfo_path = Path(args.sysinfo)
    infragraph_path = Path(args.infragraph)

    if not sysinfo_path.exists():
        print(f"[ERROR] sysinfo file not found: {sysinfo_path}", file=sys.stderr)
        sys.exit(1)
    if not infragraph_path.exists():
        print(f"[ERROR] infragraph file not found: {infragraph_path}", file=sys.stderr)
        sys.exit(1)

    with open(infragraph_path, "r", encoding="utf-8") as f:
        infra = Infrastructure().deserialize(yaml.safe_load(f))

    with open(sysinfo_path, "r", encoding="utf-8") as f:
        sysinfo = json.load(f)

    service = InfraGraphService()
    service.set_graph(infra)

    annotation = Annotation()
    # The single-node sysinfo JSON is now a flat dict of prefixed keys
    # (previously nested under hardware_ensemble.{processor,accelerator}).
    # Group by prefix to recover the processor / accelerator attribute sets.
    processor_attrs = {k: v for k, v in sysinfo.items()
                       if k.startswith("host_processor")}
    accelerator_attrs = {k: v for k, v in sysinfo.items()
                         if k.startswith("accelerator")}

    response = service.query_graph(build_type_query("cpu", "xpu"))

    for match in matched_nodes(response, "cpu"):
        node = annotation.nodes.add(name=match.name)
        for key, value in processor_attrs.items():
            node.attributes.add(attribute=key, value=str(value))

    for match in matched_nodes(response, "xpu"):
        if accelerator_attrs.get("accelerator_model_name", "") in match.name:
            node = annotation.nodes.add(name=match.name)
            for key, value in accelerator_attrs.items():
                node.attributes.add(attribute=key, value=str(value))

    service.annotate_graph(annotation)
    get_graph_req = GraphRequest()
    get_graph_req.choice = get_graph_req.INFRAGRAPH
    get_graph_req.infragraph.annotations.choice = "full"
    graph_result = service.get_graph(get_graph_req)

    output_path = sysinfo_path.parent / "infragraph_sys_info.json"
    with open(output_path, "w") as f:
        f.write(graph_result)

    print(f"[INFO] Annotated sysinfo JSON written to {output_path}")


if __name__ == "__main__":
    main()
