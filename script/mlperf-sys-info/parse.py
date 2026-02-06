import json
import re
from pathlib import Path

def parse_system_info(file_path="system-info.txt"):
    if not Path(file_path).is_file():
        print(f"Error: {file_path} not found")
        return {}

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    data = {}

    # Extract from KEY_SYSTEM_INFO section
    key_section = re.search(r"=== KEY_SYSTEM_INFO ===\n(.*?)(?=== FULL_RAW_DATA ===|$)", text, re.DOTALL)
    if key_section:
        lines = key_section.group(1).strip().splitlines()
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()

    # Derive / fix missing values
    if "host_processor_core_count" in data and "threads_per_core" in data and "host_processors_per_node" in data:
        try:
            sockets = int(data.get("host_processors_per_node", 1))
            cores = int(data["host_processor_core_count"])
            threads = int(data.get("threads_per_core", 1))
            data["host_processor_vcpu_count"] = str(sockets * cores * threads)
        except:
            pass

    # GPU fallback / cleanup
    if "accelerators_per_node" not in data or data.get("accelerators_per_node") == "0":
        gpu_count = len(re.findall(r"GPU [0-9]+:", text))
        if gpu_count > 0:
            data["accelerators_per_node"] = str(gpu_count)

    # Build your desired structure (single ensemble for simplicity; extend if multi-partition)
    result = {
        "system_size": f"{data.get('number_of_nodes', '1')}x{data.get('accelerator_model_name', 'GB200')}",
        "system_node_ensemble_count": 1,  # adjust if you detect multiple homogeneous groups
        "system_node_ensemble_total": 1,  # single node or override if cluster
        "system_nodes_details": [{
            "system_node_ensemble_id": 1,
            "number_of_nodes": 1,  # change if parsing cluster size
            "host_processor_model_name": data.get("host_processor_model_name", "NVIDIA Grace CPU"),
            "host_processors_per_node": int(data.get("host_processors_per_node", 2)),
            "host_processor_core_count": int(data.get("host_processor_core_count", 144)),
            "host_processor_vcpu_count": int(data.get("host_processor_vcpu_count", 288)),
            "accelerator_model_name": data.get("accelerator_model_name", "NVIDIA GB200"),
            "accelerators_per_node": int(data.get("accelerators_per_node", 4)),
            "accelerator_host_interconnect": data.get("accelerator_host_interconnect", "NVLink-C2C"),
            "accelerator_interconnect": data.get("accelerator_interconnect", "5th-gen NVLink and NVLink Switches"),
            "accelerator_memory_capacity": data.get("accelerator_memory_capacity", "186 GB"),
            "accelerator_memory_type": data.get("accelerator_memory_type", "HBM3e"),
            "host_memory_capacity": data.get("host_memory_capacity", "N/A"),
            "host_memory_configuration": data.get("host_memory_configuration", "1.3TB LPDDR5x"),
            "host_network_card_count": data.get("host_network_card_count", "N/A"),
            "host_networking": data.get("host_networking", "Ethernet(IPoIB)"),
            "host_storage_capacity": data.get("host_storage_capacity", "N/A"),
            "host_storage_type": data.get("host_storage_type", "NVMe SSD, CIFS mounted disk storage")
        }]
    }

    return result


if __name__ == "__main__":
    info = parse_system_info()
    print(json.dumps(info, indent=2))