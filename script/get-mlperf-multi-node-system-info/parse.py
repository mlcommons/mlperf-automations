import json
import re
import argparse
from pathlib import Path
import sys

# -------------------------------------------------------------------
# Extraction rules:
#   target_key:
#     - candidates: possible dump keys in system-info.json
#     - regex: regex applied on command output
# -------------------------------------------------------------------

EXTRACT_RULES = {
    # ---------------- CPU ----------------
    "host_processor_model_name": {
        "candidates": ["lscpu"],
        "regex": r"Model name:\s+(.*)"
    },
    "host_processors_per_node": {
        "candidates": ["lscpu"],
        "regex": r"Socket\(s\):\s+(\d+)"
    },
    "host_processor_core_count": {
        "candidates": ["lscpu"],
        "regex": r"Core\(s\) per socket:\s+(\d+)"
    },
    "host_processor_vcpu_count": {
        "candidates": ["lscpu"],
        "regex": r"CPU\(s\):\s+(\d+)"
    },

    # ---------------- Memory ----------------
    "host_memory_capacity": {
        "candidates": ["memory_free_human"],
        "regex": r"Mem:\s+([\d\.]+[A-Z]+)"
    },
    "host_memory_configuration": {
        "candidates": ["dmidecode_full"],
        "regex": r"Memory Device"
    },

    # ---------------- Accelerator ----------------
    "accelerator_model_name": {
        "candidates": ["accelerator_model_name"],
        "regex": r".*"
    },
    "accelerators_per_node": {
        "candidates": ["accelerators_per_node"],
        "regex": r".*"
    },
    "accelerator_memory_capacity": {
        "candidates": ["accelerator_memory_capacity"],
        "regex": r".*"
    },
    "accelerator_memory_type": {
        "candidates": ["accelerator_memory_type"],
        "regex": r".*"
    },
    "accelerator_interconnect": {
        "candidates": ["accelerator_interconnect"],
        "regex": r".*"
    },
    "accelerator_host_interconnect": {
        "candidates": ["accelerator_host_interconnect"],
        "regex": r".*"
    },

    # ---------------- Networking ----------------
     "host_network_card_count": {
        "candidates": ["pci_devices"],
        "regex": r"(Ethernet controller:|Network controller:|Infiniband controller:)"
    },
    "host_networking": {
        "candidates": ["host_networking"],
        "regex": r"(InfiniBand|IPoIB|RoCE|Ethernet)"
    },

    # ---------------- Storage ----------------
    "host_storage_capacity": {
        "candidates": ["lsblk", "df"],
        "regex": r"(\d+(\.\d+)?\s*(GB|TB|GiB|TiB))"
    },
    "host_storage_type": {
        "candidates": ["lsblk", "mount"],
        "regex": r"(NVMe|SSD|HDD|SATA|SAS|CIFS|NFS)"
    },
}

# -------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    return p.parse_args()

# -------------------------------------------------------------------

def extract_value(system_info, rule):
    collected = []

    for candidate in rule["candidates"]:
        for dump_key, dump in system_info.items():
            if candidate in dump_key:
                output = dump.get("output", "")
                if not output:
                    continue

                matches = re.findall(rule["regex"], output, re.IGNORECASE)

                if matches:
                    for m in matches:
                        if isinstance(m, tuple):
                            collected.append(m[0])
                        else:
                            collected.append(m)

    if not collected:
        return ""

    # Special handling: counts
    if rule["regex"] == r"(Ethernet controller:|Network controller:|Infiniband controller:)":
        return len(collected)

    # Deduplicate and join
    return ", ".join(sorted(set(collected)))

# -------------------------------------------------------------------

def main():
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"[WARN] Input file not found: {input_path}", file=sys.stderr)
        json.dump({}, open(output_path, "w"), indent=2)
        return

    with open(input_path) as f:
        system_info = json.load(f)

    parsed = {}

    for target_key, rule in EXTRACT_RULES.items():
        try:
            parsed[target_key] = extract_value(system_info, rule)
        except Exception as e:
            parsed[target_key] = ""
            print(f"[WARN] Failed to extract {target_key}: {e}", file=sys.stderr)

    with open(output_path, "w") as f:
        json.dump(parsed, f, indent=2)

    print(f"[INFO] Parsed system info written to {output_path}")

# -------------------------------------------------------------------

if __name__ == "__main__":
    main()
