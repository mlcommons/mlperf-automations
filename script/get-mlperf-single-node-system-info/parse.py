import json
import re
import argparse
from pathlib import Path
import sys
import os

# -------------------------------------------------------------------
# Extraction rules:
#   target_key:
#     - candidates: possible dump keys in system-info.json
#     - regex: regex applied on command output
# -------------------------------------------------------------------

EXTRACT_RULES = {
    # ---------------- CPU ----------------
    "host_processor_model_name": {
        "source": "env",
        "candidates": ["MLC_HOST_CPU_MODEL_NAME"],
    },
    "host_processors_per_node": {
        "source": "env",
        "candidates": ["MLC_HOST_CPU_SOCKETS"],
    },
    "host_processor_core_count": {
        "source": "env",
        "candidates": ["MLC_HOST_CPU_TOTAL_PHYSICAL_CORES"],
    },
    "host_processor_vcpu_count": {
        "source": "env",
        "candidates": ["MLC_HOST_CPU_TOTAL_LOGICAL_CORES"],
    },

    # ---------------- Memory ----------------
    "host_memory_capacity": {
        "source": "env",
        "candidates": ["MLC_HOST_MEMORY_CAPACITY"],
    },
    "host_memory_configuration": {
        "candidates": ["dmidecode_full"],
        "regex": [
            r"Size:\s+(\d+)\s+GB",
            r"Type:\s+(DDR\d+)",
            r"Speed:\s+(\d+)\s+MT/s"
        ]
    },

    # ---------------- Accelerator ----------------
    "accelerator_model_name": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_GPU_NAME"],
    },
    "accelerators_per_node": {
        "source": "env",
        "candidates": ["MLC_CUDA_NUM_DEVICES"],
    },
    "accelerator_memory_capacity": {
        "source": "env",
        # Get the value as decimal gigabytes
        "candidates": ["MLC_CUDA_DEVICE_PROP_GLOBAL_MEMORY"],
    },
    "accelerator_memory_type": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_MEMORY_TYPE"],
    },
    "accelerator_interconnect": {
        "candidates": ["nvidia_smi_topo"],
        "regex": r".*"
    },
    "accelerator_host_interconnect": {
        "candidates": [""],
        "regex": r".*"
    },

    # ---------------- Networking ----------------
    "host_network_card_count": {
        "candidates": [""],
        "regex": r".*"
    },
    "host_networking": {
        "candidates": [""],
        "regex": r".*"
    },

    # ---------------- Storage ----------------
    "host_storage_capacity": {
        "source": "env",
        "candidates": ["MLC_HOST_DISK_CAPACITY"],
    },
    "host_storage_type": {
        "candidates": ["disk_layout"],
        "regex": r".*"
    },

    # ---------------- Software Ensemble ----------------
    "framework": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_CUDA_DRIVER_VERSION", "MLC_CUDA_DEVICE_PROP_CUDA_RUNTIME_VERSION"],
        "regex": r".*"
    },
    "operating_system": {
        "source": "env",
        "candidates": ["MLC_HOST_OS_TYPE", "MLC_HOST_OS_FLAVOR_LIKE", "MLC_HOST_OS_FLAVOR", "MLC_HOST_OS_VERSION"],
    },
    "filesystem": {
        "source": "env",
        "candidates": ["MLC_HOST_FILESYSTEMS"],
    },
    "other_software_stack": {
        "candidates": [],
        "regex": r".*"
    },
    "sw_notes": {
        "candidates": [],
        "regex": r".*"
    }
}

# -------------------------------------------------------------------


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    return p.parse_args()

# -------------------------------------------------------------------


def extract_value(system_info, rule, field_key):
    def get_link_layer(device_name: str) -> str | None:
        """Returns 'InfiniBand' or 'Ethernet' (RoCE) for a given RDMA device"""
        path = f"/sys/class/infiniband/{device_name}/ports/1/link_layer"
        if not os.path.isfile(path):
            return None
        with open(path, "r") as f:
            return f.read().strip()

    collected = []

    if rule.get("source", "") == "env":
        value = ""

        if field_key == "framework":
            value = ""
            for candidate in rule["candidates"]:
                print(candidate)
                env_output = os.environ.get(candidate, "")
                if env_output:
                    if "cuda_runtime" in candidate.lower():
                        value += f"Cuda runtime version {env_output} ; "
                    elif "cuda_driver" in candidate.lower():
                        value += f"Cuda driver version {env_output} ; "
            return value

        for candidate in rule["candidates"]:
            value += f" {os.environ.get(candidate, '')}"
            if field_key == "accelerator_memory_capacity":
                value_bytes = float(os.environ.get(candidate, ""))
                if value_bytes == "":
                    return ""
                else:
                    # get as decimal gigabytes as marketed by the vendors
                    return f"{int(value_bytes/(1000**3))}GB"

        return value.strip()
    else:
        for candidate in rule["candidates"]:
            for dump_key, dump in system_info.items():
                if candidate in dump_key:
                    output = dump.get("output", "")
                    if not output:
                        continue

                    # Handle list of regex (for derived fields)
                    regex_list = rule["regex"] if isinstance(
                        rule["regex"], list) else [rule["regex"]]

                    for regex in regex_list:
                        matches = re.findall(regex, output, re.IGNORECASE)

                        if matches:
                            for m in matches:
                                if isinstance(m, tuple):
                                    collected.append(m[0].strip())
                                else:
                                    collected.append(m.strip())

        if not collected and field_key not in [
                "host_memory_configuration", "accelerator_interconnect", "host_network_card_count", "host_networking", "host_storage_type"]:
            return ""

        if field_key == "host_storage_type":
            output = ""
            for candidate in rule["candidates"]:
                for dump_key, dump in system_info.items():
                    if candidate in dump_key.lower():  # case-insensitive match
                        output = dump.get("output", "").strip()
                        break
                if output:
                    break

            if not output:
                return "No disk layout data found"

            types_found = set()

            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue

                # Split on whitespace — columns are space-separated
                parts = re.split(r'\s+', line)

                if len(parts) < 5:
                    continue  # too short → skip garbage

                name = parts[0]
                dev_type = parts[1]
                size = parts[2]
                # model may contain spaces → join until we reach the last two columns
                # last two are TRAN and ROTA (VENDOR may be missing or
                # multi-word)
                tran = parts[-2] if len(parts) >= 6 else "unknown"
                rota = parts[-1] if len(parts) >= 6 else "unknown"

                if dev_type != "disk":
                    continue

                # Core classification
                if name.startswith("nvme") or tran == "nvme":
                    types_found.add("NVMe SSD")
                elif rota == "0":
                    types_found.add("SSD")           # usually SATA SSD
                elif rota == "1":
                    types_found.add("HDD")
                else:
                    # rare fallback — look at model if available
                    model_start = 3
                    model_end = len(parts) - 2
                    model = " ".join(
                        parts[model_start:model_end]) if model_end > model_start else ""
                    if "SSD" in model.upper():
                        types_found.add("SSD")
                    elif "HDD" in model.upper() or any(x in model for x in ["ST", "WD", "HGST", "Toshiba", "Seagate"]):
                        types_found.add("HDD")
                    else:
                        types_found.add("Other")

            if not types_found:
                return "No physical disks detected"

            # Order them nicely
            ordered = []
            for t in ["NVMe SSD", "SSD", "HDD", "Other"]:
                if t in types_found:
                    ordered.append(t)

            return " + ".join(ordered)

        if field_key == "host_networking":
            if not os.path.isdir("/sys/class/infiniband"):
                return "Ethernet"
            devices = os.listdir("/sys/class/infiniband")
            results = []
            for dev in devices:
                ll = get_link_layer(dev)
                if ll == "InfiniBand":
                    results.append(f"{dev}: native InfiniBand")
                elif ll == "Ethernet":
                    results.append(f"{dev}: RoCE (RDMA over Ethernet)")
                else:
                    results.append(f"{dev}: unknown mode")
            if not results:
                return "RDMA devices found but no link layer info"
            return "; ".join(results)

        if field_key == "host_network_card_count":
            count = 0
            for ifname in os.listdir("/sys/class/net"):
                if ifname == 'lo':
                    continue
                device_link = f"/sys/class/net/{ifname}/device"
                if os.path.islink(device_link):
                    target = os.readlink(device_link)
                    if '/virtual/' not in target:
                        count += 1
            return str(count)

        if field_key == "accelerator_interconnect":
            topo_output = ""
            for candidate in rule["candidates"]:
                for dump_key, dump in system_info.items():
                    if candidate in dump_key:
                        topo_output = dump.get("output", "")
                        break

            if not topo_output:
                return ""

            if re.search(r"\bNV\d+\b", topo_output):
                return "NVLink"

            return "PCIe"

        if field_key == "accelerator_host_interconnect":
            smi_output = ""
            for dump_key, dump in system_info.items():
                if "nvidia_smi_full" in dump_key:
                    smi_output = dump.get("output", "")
                    break

            if not smi_output:
                return ""

            gen_match = re.search(
                r"PCIe Generation\s*\n\s*Max\s*:\s*\d+\s*\n\s*Current\s*:\s*(\d+)",
                smi_output)
            width_match = re.search(
                r"Link Width\s*\n\s*Max\s*:\s*\d+x\s*\n\s*Current\s*:\s*(\d+)x",
                smi_output)

            if gen_match and width_match:
                return f"PCIe Gen{gen_match.group(1)} x{width_match.group(1)}"

            return "PCIe"

        if field_key == "host_memory_configuration":
            try:
                # Find full dmidecode output
                dmidecode_output = ""
                for candidate in rule["candidates"]:
                    for dump_key, dump in system_info.items():
                        if candidate in dump_key:
                            dmidecode_output = dump.get("output", "")
                            break

                if not dmidecode_output:
                    return ""

                dimm_blocks = re.split(
                    r"Memory Device",
                    dmidecode_output,
                    flags=re.IGNORECASE)

                sizes = []
                types = []
                speeds = []

                for block in dimm_blocks:
                    if "No Module Installed" in block:
                        continue

                    size_match = re.search(
                        r"Size:\s+(\d+)\s+GB", block, re.IGNORECASE)
                    type_match = re.search(
                        r"Type:\s+(DDR\d+)", block, re.IGNORECASE)
                    speed_match = re.search(
                        r"(Configured Clock Speed|Speed):\s+(\d+)\s+MT/s", block, re.IGNORECASE)

                    if size_match:
                        sizes.append(size_match.group(1))

                        if type_match:
                            types.append(type_match.group(1))

                        if speed_match:
                            speeds.append(speed_match.group(2))

                if not sizes:
                    return ""

                dimm_count = len(sizes)
                dimm_size = sizes[0]
                dimm_type = types[0] if types else ""
                dimm_speed = speeds[0] if speeds else ""

                return f"{dimm_count} x {dimm_size}GB {dimm_type}-{dimm_speed}".rstrip(
                    "-")

            except Exception:
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
            ensemble_type_subpart = ""
            # get ensemble type subpart
            if target_key in ["host_processor_model_name", "host_processors_per_node",
                              "host_processor_core_count", "host_processor_vcpu_count"]:
                ensemble_type_subpart = "processor"
            elif target_key in ["host_memory_capacity", "host_memory_configuration"]:
                ensemble_type_subpart = "host_memory"
            elif target_key in ["accelerator_model_name", "accelerators_per_node", "accelerator_memory_capacity", "accelerator_memory_type", "accelerator_interconnect", "accelerator_host_interconnect"]:
                ensemble_type_subpart = "accelerator"
            elif target_key in ["host_network_card_count", "host_networking"]:
                ensemble_type_subpart = "networking"
            elif target_key in ["host_storage_capacity", "host_storage_type"]:
                ensemble_type_subpart = "storage"
            elif target_key in ["other_hardware", "cooling", "hw_notes"]:
                ensemble_type_subpart = "other"

            # get ensemble type
            if ensemble_type_subpart in [
                    "processor", "host_memory", "accelerator", "networking", "storage", "other"]:
                ensemble_type = "hardware_ensemble"
                if ensemble_type not in parsed:
                    parsed[ensemble_type] = {}
                if ensemble_type_subpart not in parsed[ensemble_type]:
                    parsed[ensemble_type][ensemble_type_subpart] = {}
                parsed[ensemble_type][ensemble_type_subpart][target_key] = extract_value(
                    system_info, rule, target_key)
            elif target_key in ["framework", "operating_system", "filesystem", "other_software_stack", "sw_notes"]:
                ensemble_type = "software_ensemble"
                if ensemble_type not in parsed:
                    parsed[ensemble_type] = {}
                parsed[ensemble_type][target_key] = extract_value(
                    system_info, rule, target_key)
        except Exception as e:
            parsed[target_key] = ""
            print(
                f"[WARN] Failed to extract {target_key}: {e}",
                file=sys.stderr)

    with open(output_path, "w") as f:
        json.dump(parsed, f, indent=2)

    print(f"[INFO] Parsed system info written to {output_path}")

# -------------------------------------------------------------------


if __name__ == "__main__":
    main()
