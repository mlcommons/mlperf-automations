import json
import argparse
import math
import re
import subprocess
from pathlib import Path
import sys
import os

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')

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
    "host_processor_frequency": {
        # detect-cpu exposes the max clock as MLC_HOST_CPU_MAX_MHZ.
        "source": "env",
        "candidates": ["MLC_HOST_CPU_MAX_MHZ"],
    },
    "host_processor_caches": {
        # Composed from the per-level cache size vars emitted by detect-cpu.
        "source": "detect",
        "candidates": [],
    },
    "host_processor_interconnect": {
        # No script currently probes CPU-socket interconnect (e.g. UPI/Infinity
        # Fabric); left optional so it returns "" (manual field) rather than
        # "N/A".
        "source": "env",
        "candidates": ["MLC_HOST_CPU_INTERCONNECT"],
        "optional": True,
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
    "accelerator_frequency": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_MAX_CLOCK_RATE", "MLC_ROCM_DEVICE_PROP_MAX_CLOCK_RATE"],
    },
    "accelerator_memory_configuration": {
        "source": "detect",
        "candidates": [],
    },
    "accelerator_on-chip_memories": {
        "source": "detect",
        "candidates": [],
    },
    "accelerator_interconnect_topology": {
        "source": "env",
        "candidates": ["MLC_CUDA_DEVICE_PROP_GPU_TOPOLOGY_DESC"],
        "optional": True,
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
        "source": "env",
        "candidates": ["MLC_MLPERF_SERVING_FRAMEWORK"],
        "optional": True,
    },
    "inference_backend": {
        "source": "detect",
        "candidates": [],
    },
    "driver": {
        "source": "env",
        "candidates": ["MLC_HOST_GPU_DRIVER_VERSION"],
    },
    "operating_system": {
        "source": "env",
        "candidates": ["MLC_HOST_OS_FLAVOR", "MLC_HOST_OS_VERSION"],
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
        "source": "detect",
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


# -------------------------------------------------------------------


def extract_value(rule, field_key):
    """Return the field value on success, or a human-readable reason string on failure.
    Optional fields return None when empty (no reason string).
    Int-typed fields return an int on success or a reason string on failure.
    """
    if rule.get("source") == "detect":
        try:
            if field_key == "inference_backend":
                v = detect_inference_backend()
                return v if v else "Not detected: CUDA/ROCm/XPU runtime not found"
            elif field_key == "other_software_stack":
                stack_parts = []
                backend = detect_inference_backend()
                if backend:
                    stack_parts.append(backend)
                driver = os.environ.get(
                    "MLC_HOST_GPU_DRIVER_VERSION", "").strip()
                if driver:
                    stack_parts.append(driver)
                return ", ".join(stack_parts) if stack_parts else ""
            elif field_key == "accelerator_memory_configuration":
                mem_bytes_str = os.environ.get(
                    "MLC_CUDA_DEVICE_PROP_GLOBAL_MEMORY", "").strip()
                mem_type = os.environ.get(
                    "MLC_CUDA_DEVICE_PROP_MEMORY_TYPE", "").strip()
                parts = []
                if mem_bytes_str:
                    try:
                        mem_bytes = float(mem_bytes_str.split()[0])
                        if mem_bytes >= 1024 ** 3:
                            parts.append(
                                f"{math.ceil(mem_bytes / (1024 ** 3))} GiB")
                    except (ValueError, IndexError):
                        pass
                if mem_type and "unknown" not in mem_type.lower() \
                        and "not in lookup" not in mem_type.lower():
                    parts.append(mem_type)
                return " ".join(parts) if parts else "N/A"
            elif field_key == "host_processor_caches":
                cache_levels = [
                    ("L1d", "MLC_HOST_CPU_L1D_CACHE_SIZE"),
                    ("L1i", "MLC_HOST_CPU_L1I_CACHE_SIZE"),
                    ("L2", "MLC_HOST_CPU_L2_CACHE_SIZE"),
                    ("L3", "MLC_HOST_CPU_L3_CACHE_SIZE"),
                ]
                parts = []
                for label, key in cache_levels:
                    v = os.environ.get(key, "").strip()
                    if v:
                        parts.append(f"{label}: {v}")
                return "; ".join(parts) if parts else "N/A"
            elif field_key == "accelerator_on-chip_memories":
                shared_str = os.environ.get(
                    "MLC_CUDA_DEVICE_PROP_TOTAL_AMOUNT_OF_SHARED_MEMORY_PER_BLOCK",
                    "").strip()
                if shared_str:
                    try:
                        kb = int(shared_str) // 1024
                        return f"Shared Memory: {kb} KB/block"
                    except (ValueError, TypeError):
                        pass
                return "N/A"
            else:
                return "N/A"
        except Exception as e:
            return f"Not detected: {field_key} detection error ({e})"

    # Collect non-empty env var values.
    # Strip ANSI escape codes defensively: some tools (e.g. nvidia-smi topo -m)
    # emit colour sequences when run in an interactive terminal. Those codes can
    # end up stored in the mlcflow cache and resurface here as literal garbage
    # characters in the output JSON. The primary stripping happens at capture
    # time in get-cuda-devices/customize.py; this call handles any stale cached
    # values that predate that fix.
    candidates = rule.get("candidates", [])
    parts = [os.environ.get(c, "") for c in candidates]
    value = _ANSI_RE.sub('', " ".join(p for p in parts if p)).strip()

    if field_key == "host_processor_frequency":
        if not value:
            return "N/A"
        # MLC_HOST_CPU_MAX_MHZ is a bare MHz figure (e.g. "5137.0000").
        try:
            mhz = float(value.split()[0])
        except (ValueError, IndexError):
            return value
        if mhz >= 1000:
            return f"{mhz / 1000:.2f} GHz"
        return f"{int(round(mhz))} MHz"

    if field_key == "accelerators_per_node":
        nums = [int(x) for x in value.split() if x.isdigit()]
        return sum(nums) if nums else "N/A"

    if field_key == "host_network_card_count":
        networking = os.environ.get("MLC_HOST_NETWORKING", "").strip()
        if value and networking:
            return f"{value}x {networking}"
        if value:
            return f"{value}x"
        return "N/A"

    if field_key == "accelerator_memory_capacity":
        if not value:
            return "N/A"
        raw = value.split()[0]
        try:
            value_bytes = float(raw)
        except ValueError:
            return "N/A"
        if value_bytes == 0:
            return "N/A"
        # Report in GiB (binary) using ceil to align with GPU product marketing values.
        # CUDA global memory is slightly below the marketed GiB due to driver reservation;
        # ceil absorbs that gap so e.g. 31.37 GiB → 32 GiB (matching "32 GB" on
        # the box).
        if value_bytes >= 1024 ** 3:
            return f"{math.ceil(value_bytes / (1024 ** 3))}GiB"
        # Value is already in GiB (e.g. from MLC_ROCM_DEVICE_PROP_GLOBAL_MEMORY_IN_GIB)
        return f"{math.ceil(value_bytes)}GiB"

    if field_key == "host_storage_type" and value == "No disk layout data found":
        return "N/A"

    if rule.get("type") == "int":
        if not value:
            return "N/A"
        try:
            return int(value)
        except (ValueError, TypeError):
            return "N/A"

    if rule.get("optional"):
        return value if value else ""

    return value if value else "N/A"

# -------------------------------------------------------------------


def main():
    args = parse_args()

    output_path = Path(args.output)

    parsed = {}

    for target_key, rule in EXTRACT_RULES.items():
        try:
            parsed[target_key] = extract_value(rule, target_key)
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
