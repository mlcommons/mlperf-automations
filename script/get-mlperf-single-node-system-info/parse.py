import json
import argparse
from pathlib import Path
import sys
import os

# -------------------------------------------------------------------
# Extraction rules: all data comes from environment variables.
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
        "source": "env",
        "candidates": ["MLC_HOST_MEMORY_CONFIGURATION"],
    },

    # ---------------- Accelerator ----------------
    "accelerator_model_name": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_GPU_NAME", "MLC_ROCM_DEVICE_PROP_GPU_NAME", "MLC_XPU_DEVICE_PROP_GPU_NAME"],
    },
    "accelerators_per_node": {
        "source": "env",
        "candidates": ["MLC_CUDA_NUM_DEVICES", "MLC_ROCM_NUM_DEVICES", "MLC_XPU_NUM_DEVICES"],
    },
    "accelerator_memory_capacity": {
        "source": "env",
        # Get the value as decimal gigabytes
        "candidates": ["MLC_CUDA_DEVICE_PROP_GLOBAL_MEMORY", "MLC_ROCM_DEVICE_PROP_GLOBAL_MEMORY_IN_GIB", "MLC_XPU_DEVICE_PROP_GLOBAL_MEMORY"],
    },
    "accelerator_memory_type": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_MEMORY_TYPE",  "MLC_XPU_DEVICE_PROP_MEMORY_TYPE"],
    },
    "accelerator_interconnect": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_GPU_INTERCONNECT_TYPE", "MLC_ROCM_DEVICE_PROP_GPU_INTERCONNECT_TYPE", "MLC_XPU_DEVICE_PROP_GPU_INTERCONNECT_TYPE"],
    },
    "accelerator_host_interconnect": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_HOST_INTERCONNECT_TYPE", "MLC_ROCM_DEVICE_PROP_HOST_INTERCONNECT_TYPE", "MLC_XPU_DEVICE_PROP_HOST_INTERCONNECT_TYPE"],
    },

    "accelerator_frequency": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_MAX_CLOCK_RATE", "MLC_ROCM_DEVICE_PROP_MAX_CLOCK_RATE", "MLC_XPU_DEVICE_PROP_MAX_CLOCK_RATE"],
    },

    # ---------------- Networking ----------------
    "host_network_card_count": {
        "source": "env",
        "candidates": ["MLC_HOST_NETWORK_CARD_COUNT"],
    },
    "host_networking": {
        "source": "env",
        "candidates": ["MLC_HOST_NETWORKING"],
    },

    # ---------------- Storage ----------------
    "host_storage_capacity": {
        "source": "env",
        "candidates": ["MLC_HOST_DISK_CAPACITY"],
    },
    "host_storage_type": {
        "source": "env",
        "candidates": ["MLC_HOST_STORAGE_TYPE"],
    },

    # ---------------- Software Ensemble ----------------
    "framework": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_CUDA_DRIVER_VERSION", "MLC_CUDA_DEVICE_PROP_CUDA_RUNTIME_VERSION"],
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
        "source": "env",
        "candidates": [],
    },
    "sw_notes": {
        "source": "env",
        "candidates": [],
    }
}

# -------------------------------------------------------------------


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    return p.parse_args()

# -------------------------------------------------------------------


def extract_value(rule, field_key):
    value = ""

    if field_key == "framework":
        for candidate in rule["candidates"]:
            env_output = os.environ.get(candidate, "")
            if env_output:
                if "cuda_runtime" in candidate.lower():
                    value += f"Cuda runtime version {env_output} ; "
                elif "cuda_driver" in candidate.lower():
                    value += f"Cuda driver version {env_output} ; "
        return value

    for candidate in rule["candidates"]:
        value += f" {os.environ.get(candidate, '')}"

    if field_key == "accelerators_per_node":
        value = sum(int(elem) for elem in value.split() if elem.isdigit())
        return str(value)

    if field_key == "accelerator_memory_capacity":
        value = value.strip()
        if len(value.split()) == 2:
            value = value.split()[0]
        if not value:
            return ""
        value_bytes = float(value)
        if value_bytes == 0:
            return ""
        # get as decimal gigabytes as marketed by the vendors
        if value_bytes >= 1000**3:
            return f"{int(value_bytes/(1000**3))}GB"
        else:
            return f"{int(value_bytes)}GB"

    return value.strip()

# -------------------------------------------------------------------


def main():
    args = parse_args()

    output_path = Path(args.output)

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
            elif target_key in ["accelerator_frequency"]:
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
                    rule, target_key)
            elif target_key in ["framework", "operating_system", "filesystem", "other_software_stack", "sw_notes"]:
                ensemble_type = "software_ensemble"
                if ensemble_type not in parsed:
                    parsed[ensemble_type] = {}
                parsed[ensemble_type][target_key] = extract_value(
                    rule, target_key)
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
