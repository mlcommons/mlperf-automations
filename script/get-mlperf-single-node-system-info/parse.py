import json
import argparse
import math
import subprocess
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
        "type": "int",
    },
    "host_processor_core_count": {
        "source": "env",
        "candidates": ["MLC_HOST_CPU_TOTAL_PHYSICAL_CORES"],
        "type": "int",
    },
    "host_processor_vcpu_count": {
        "source": "env",
        "candidates": ["MLC_HOST_CPU_TOTAL_LOGICAL_CORES"],
        "type": "int",
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
        "candidates": ["MLC_CUDA_DEVICE_PROP_MEMORY_TYPE", "MLC_XPU_DEVICE_PROP_MEMORY_TYPE"],
    },
    "accelerator_interconnect": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_GPU_INTERCONNECT_TYPE", "MLC_ROCM_DEVICE_PROP_GPU_INTERCONNECT_TYPE", "MLC_XPU_DEVICE_PROP_GPU_INTERCONNECT_TYPE"],
    },
    "accelerator_host_interconnect": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_HOST_INTERCONNECT_TYPE", "MLC_ROCM_DEVICE_PROP_HOST_INTERCONNECT_TYPE", "MLC_XPU_DEVICE_PROP_HOST_INTERCONNECT_TYPE"],
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

    # ---------------- Other hardware metadata ----------------
    "other_hardware": {
        "source": "env",
        "candidates": ["MLC_MLPERF_OTHER_HARDWARE"],
        "optional": True,
    },
    "hw_notes": {
        "source": "env",
        "candidates": ["MLC_MLPERF_HARDWARE_NOTES"],
        "optional": True,
    },
    "cooling": {
        "source": "env",
        "candidates": ["MLC_MLPERF_COOLING"],
        "optional": True,
    },

    # ---------------- Software Ensemble ----------------
    "serving_framework": {
        "source": "detect",
        "candidates": [],
    },
    "inference_backend": {
        "source": "detect",
        "candidates": [],
    },
    "driver": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_CUDA_DRIVER_VERSION", "MLC_ROCM_DEVICE_PROP_ROCM_DRIVER_VERSION"],
    },
    "operating_system": {
        "source": "env",
        "candidates": ["MLC_HOST_OS_TYPE", "MLC_HOST_OS_FLAVOR_LIKE", "MLC_HOST_OS_FLAVOR", "MLC_HOST_OS_VERSION"],
    },
    "filesystem": {
        "source": "env",
        "candidates": ["MLC_HOST_FILESYSTEMS"],
    },
    "container_link": {
        "source": "env",
        "candidates": ["MLC_MLPERF_CONTAINER_LINK"],
        "optional": True,
    },
    "other_software_stack": {
        "source": "env",
        "candidates": [],
        "optional": True,
    },
    "sw_notes": {
        "source": "env",
        "candidates": [],
        "optional": True,
    }
}

# -------------------------------------------------------------------


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    return p.parse_args()

# -------------------------------------------------------------------


def _run(cmd, timeout=10):
    try:
        return subprocess.run(cmd, capture_output=True,
                              text=True, timeout=timeout)
    except Exception:
        return None


def _pip_version(package):
    r = _run(["pip", "show", package])
    if r and r.returncode == 0:
        for line in r.stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    return None


def detect_serving_framework():
    """Detect installed serving frameworks: vLLM, SGLang, TensorRT-LLM."""
    found = []

    v = _pip_version("vllm")
    if v:
        found.append(f"vLLM v{v}")

    v = _pip_version("sglang")
    if v:
        found.append(f"SGLang v{v}")

    v = _pip_version("tensorrt_llm") or _pip_version("tensorrt-llm")
    if v:
        found.append(f"TRT-LLM v{v}")

    return ", ".join(found)


def detect_inference_backend():
    """Build inference backend string from CUDA/ROCm + cuDNN versions."""
    parts = []

    cuda_runtime = os.environ.get(
        "MLC_CUDA_DEVICE_PROP_CUDA_RUNTIME_VERSION", "")
    if cuda_runtime:
        parts.append(f"CUDA {cuda_runtime}")

    rocm_version = (os.environ.get("MLC_ROCM_VERSION", "")
                    or os.environ.get("MLC_ROCM_DEVICE_PROP_ROCM_VERSION", ""))
    if rocm_version:
        parts.append(f"ROCm {rocm_version}")

    cudnn_version = None
    for pkg in ("nvidia-cudnn-cu12", "nvidia-cudnn-cu11", "cudnn"):
        cudnn_version = _pip_version(pkg)
        if cudnn_version:
            break
    if cudnn_version:
        parts.append(f"cuDNN {cudnn_version}")

    return ", ".join(parts)


# Human-readable reasons for fields that cannot be captured.
_NOT_CAPTURED = {
    "host_processor_model_name": "Not detected: CPU model name unavailable",
    "host_processors_per_node": "Not detected: CPU socket count unavailable",
    "host_processor_core_count": "Not detected: CPU core count unavailable",
    "host_processor_vcpu_count": "Not detected: vCPU count unavailable",
    "host_memory_capacity": "Not detected: Memory capacity unavailable",
    "host_memory_configuration": "Not detected: SUDO access required for DIMM configuration (dmidecode)",
    "accelerator_model_name": "Not detected: No GPU/accelerator drivers found",
    "accelerators_per_node": "Not detected: No GPU/accelerator drivers found",
    "accelerator_memory_capacity": "Not detected: No GPU/accelerator drivers found",
    "accelerator_memory_type": "Not detected: No GPU/accelerator drivers found",
    "accelerator_interconnect": "Not detected: No GPU/accelerator drivers found",
    "accelerator_host_interconnect": "Not detected: No GPU/accelerator drivers found",
    "host_network_card_count": "Not detected: Network interface information unavailable",
    "host_networking": "Not detected: Network interface information unavailable",
    "host_storage_capacity": "Not detected: Storage information unavailable",
    "host_storage_type": "Not detected: No disk layout data found",
    "serving_framework": "Not detected: No supported serving framework installed (vLLM, SGLang, TRT-LLM)",
    "inference_backend": "Not detected: No CUDA/ROCm/XPU environment found",
    "driver": "Not detected: No GPU driver version found in device properties",
    "operating_system": "Not detected: OS information unavailable",
    "filesystem": "Not detected: Filesystem information unavailable",
}

# -------------------------------------------------------------------


def extract_value(rule, field_key):
    """Return the field value on success, or a human-readable reason string on failure.
    Optional fields return None when empty (no reason string).
    Int-typed fields return an int on success or a reason string on failure.
    """
    not_captured = _NOT_CAPTURED.get(field_key, "Not detected")

    if rule.get("source") == "detect":
        try:
            if field_key == "serving_framework":
                v = detect_serving_framework()
            elif field_key == "inference_backend":
                v = detect_inference_backend()
            else:
                return not_captured
            return v if v else not_captured
        except Exception:
            return not_captured

    # Collect non-empty env var values
    parts = [os.environ.get(c, "") for c in rule.get("candidates", [])]
    value = " ".join(p for p in parts if p).strip()

    if field_key == "driver":
        cuda_ver = os.environ.get(
            "MLC_CUDA_DEVICE_PROP_CUDA_DRIVER_VERSION", "").strip()
        if cuda_ver:
            return f"Driver {cuda_ver}"
        rocm_ver = os.environ.get(
            "MLC_ROCM_DEVICE_PROP_ROCM_DRIVER_VERSION", "").strip()
        if rocm_ver:
            return f"ROCm Driver {rocm_ver}"
        return not_captured

    if field_key == "accelerators_per_node":
        nums = [int(x) for x in value.split() if x.isdigit()]
        return sum(nums) if nums else not_captured

    if field_key == "host_network_card_count":
        networking = os.environ.get("MLC_HOST_NETWORKING", "").strip()
        if value and networking:
            return f"{value}x {networking}"
        if value:
            return f"{value}x"
        return not_captured

    if field_key == "accelerator_memory_capacity":
        if not value:
            return not_captured
        raw = value.split()[0]
        try:
            value_bytes = float(raw)
        except ValueError:
            return not_captured
        if value_bytes == 0:
            return not_captured
        # Report in GiB (binary) using ceil to align with GPU product marketing values.
        # CUDA global memory is slightly below the marketed GiB due to driver reservation;
        # ceil absorbs that gap so e.g. 31.37 GiB → 32 GiB (matching "32 GB" on
        # the box).
        if value_bytes >= 1024 ** 3:
            return f"{math.ceil(value_bytes / (1024 ** 3))}GiB"
        return f"{int(value_bytes)}GiB"

    if field_key == "host_storage_type" and value == "No disk layout data found":
        return not_captured

    if rule.get("type") == "int":
        if not value:
            return not_captured
        try:
            return int(value)
        except (ValueError, TypeError):
            return not_captured

    if rule.get("optional"):
        return value if value else None

    return value if value else not_captured

# -------------------------------------------------------------------


def main():
    args = parse_args()

    output_path = Path(args.output)

    parsed = {}

    for target_key, rule in EXTRACT_RULES.items():
        try:
            ensemble_type_subpart = ""
            if target_key in ["host_processor_model_name", "host_processors_per_node",
                              "host_processor_core_count", "host_processor_vcpu_count"]:
                ensemble_type_subpart = "processor"
            elif target_key in ["host_memory_capacity", "host_memory_configuration"]:
                ensemble_type_subpart = "host_memory"
            elif target_key in ["accelerator_model_name", "accelerators_per_node",
                                "accelerator_memory_capacity", "accelerator_memory_type",
                                "accelerator_interconnect", "accelerator_host_interconnect"]:
                ensemble_type_subpart = "accelerator"
            elif target_key in ["host_network_card_count", "host_networking"]:
                ensemble_type_subpart = "networking"
            elif target_key in ["host_storage_capacity", "host_storage_type"]:
                ensemble_type_subpart = "storage"

            value = extract_value(rule, target_key)

            if target_key in ["other_hardware", "cooling", "hw_notes"]:
                parsed.setdefault("hardware_ensemble", {})[target_key] = value
            elif ensemble_type_subpart in [
                    "processor", "host_memory", "accelerator", "networking", "storage"]:
                parsed.setdefault("hardware_ensemble", {}).setdefault(
                    ensemble_type_subpart, {})[target_key] = value
            elif target_key in ["serving_framework", "inference_backend", "driver",
                                "operating_system", "filesystem", "container_link",
                                "other_software_stack", "sw_notes"]:
                parsed.setdefault("software_ensemble", {})[target_key] = value
        except Exception as e:
            parsed[target_key] = f"Not detected: extraction error ({e})"
            print(
                f"[WARN] Failed to extract {target_key}: {e}",
                file=sys.stderr)

    with open(output_path, "w") as f:
        json.dump(parsed, f, indent=2)

    print(f"[INFO] Parsed system info written to {output_path}")

# -------------------------------------------------------------------


if __name__ == "__main__":
    main()
