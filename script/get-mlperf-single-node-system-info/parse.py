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
        "source": "detect",
        "candidates": [],
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
        "source": "detect",
        "candidates": [],
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


_NETWORK_FSTYPES = frozenset([
    'cifs', 'smb3', 'smbfs', 'nfs', 'nfs4', 'nfs3',
    'glusterfs', 'fuse.glusterfs', 'lustre', 'davfs', 'fuse.sshfs',
])

_SKIP_FSTYPES = frozenset([
    'tmpfs', 'devtmpfs', 'overlay', 'proc', 'sysfs', 'cgroup', 'cgroup2',
    'pstore', 'securityfs', 'debugfs', 'tracefs', 'bpf', 'hugetlbfs',
    'mqueue', 'configfs', 'fusectl', 'efivarfs', 'binfmt_misc', 'squashfs',
    'iso9660', 'devpts', 'ramfs', 'rpc_pipefs', 'sunrpc', 'autofs', 'fuse',
    'udev',
])


def _parse_df_size(s):
    """Parse a df -h size string ('1.8T', '455G') to bytes (1024-based)."""
    import re as _re
    m = _re.match(r'^(\d+(?:\.\d+)?)([TGMKB]?)$', s.strip(), _re.IGNORECASE)
    if not m:
        return 0
    val = float(m.group(1))
    unit = m.group(2).upper()
    return int(val * {'T': 1024**4, 'G': 1024**3, 'M': 1024**2,
                      'K': 1024, 'B': 1, '': 1}.get(unit, 1))


def _bytes_to_str(n):
    """Format bytes to a size string using 1024-based units, 1 decimal place."""
    for unit, div in [('TB', 1024**4), ('GB', 1024**3), ('MB', 1024**2)]:
        if n >= div:
            s = f"{n / div:.1f}"
            if s.endswith('.0'):
                s = s[:-2]
            return f"{s} {unit}"
    return f"{n} B"


def _local_storage_type(device):
    """Return 'NVMe SSD', 'SSD', or 'HDD' for a local /dev/ device."""
    if os.path.basename(device).startswith('nvme'):
        return 'NVMe SSD'
    # Direct lsblk lookup (works for most partitions)
    try:
        r = subprocess.run(
            ['lsblk', '-n', '-o', 'ROTA,TRAN', device],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().splitlines()[0].split()
            rota = parts[0] if parts else ''
            tran = parts[1] if len(parts) > 1 else ''
            if tran == 'nvme':
                return 'NVMe SSD'
            if rota == '0':
                return 'SSD'
            if rota == '1':
                return 'HDD'
    except Exception:
        pass
    # LVM/RAID/mapper: trace back to the underlying physical disk
    try:
        r = subprocess.run(
            ['lsblk', '-n', '-s', '-o', 'NAME,TYPE,ROTA,TRAN', device],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            for line in r.stdout.strip().splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'disk':
                    name = parts[0]
                    rota = parts[2] if len(parts) > 2 else ''
                    tran = parts[3] if len(parts) > 3 else ''
                    if name.startswith('nvme') or tran == 'nvme':
                        return 'NVMe SSD'
                    if rota == '0':
                        return 'SSD'
                    if rota == '1':
                        return 'HDD'
    except Exception:
        pass
    return 'SSD'


def detect_storage_capacity():
    """Return a storage summary string e.g. '1.8 TB NVMe SSD, 5 TB CIFS'.

    Classifies local /dev/ mounts as NVMe SSD/SSD/HDD via lsblk and network
    mounts (cifs, nfs, etc.) by their filesystem type. Sums sizes per type.
    """
    try:
        r = subprocess.run(
            ['df', '-T', '-h', '--output=source,fstype,size,target'],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        r = None

    rows = []  # (source, fstype, size_str)
    if r is not None and r.returncode == 0:
        for line in r.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 3:
                rows.append((parts[0], parts[1], parts[2]))
    else:
        # Fallback: df -T -h (no --output)
        try:
            r = subprocess.run(['df', '-T', '-h'],
                               capture_output=True, text=True, timeout=10)
        except Exception:
            return ''
        if not r or r.returncode != 0:
            return ''
        for line in r.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 7:          # Filesystem Type Size Used Avail Use% Mount
                rows.append((parts[0], parts[1], parts[2]))

    type_bytes: dict = {}
    for source, fstype, size_str in rows:
        ft = fstype.lower()
        if ft in _SKIP_FSTYPES:
            continue
        if ft in _NETWORK_FSTYPES:
            storage_type = fstype.upper()
        elif source.startswith('/dev/'):
            storage_type = _local_storage_type(source)
        else:
            continue
        size_bytes = _parse_df_size(size_str)
        if size_bytes > 0:
            type_bytes[storage_type] = type_bytes.get(
                storage_type, 0) + size_bytes

    if not type_bytes:
        return ''

    order = ['NVMe SSD', 'SSD', 'HDD']
    parts = [f"{_bytes_to_str(type_bytes[t])} {t}"
             for t in order if t in type_bytes]
    for t in sorted(type_bytes):
        if t not in order:
            parts.append(f"{_bytes_to_str(type_bytes[t])} {t}")
    return ', '.join(parts)


def detect_driver():
    """Detect GPU kernel driver version (NVIDIA or AMD)."""
    r = _run(["nvidia-smi",
              "--query-gpu=driver_version",
              "--format=csv,noheader"])
    if r and r.returncode == 0 and r.stdout.strip():
        version = r.stdout.strip().splitlines()[0].strip()
        if version:
            return f"Driver {version}"

    r = _run(["rocm-smi", "--showdriverversion"])
    if r and r.returncode == 0 and r.stdout.strip():
        for line in r.stdout.splitlines():
            if "driver" in line.lower() and "version" in line.lower():
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return f"ROCm Driver {parts[1].strip()}"

    return ""

# -------------------------------------------------------------------


def extract_value(rule, field_key):
    """Return (value, note). note is None on success; a string explaining why on failure.
    Optional fields return (None, None) when empty — no note added.
    """
    if rule.get("source") == "detect":
        try:
            if field_key == "serving_framework":
                v = detect_serving_framework()
            elif field_key == "inference_backend":
                v = detect_inference_backend()
            elif field_key == "driver":
                v = detect_driver()
            elif field_key == "host_storage_capacity":
                v = detect_storage_capacity()
            else:
                return None, "Unknown detect target"
            return (v, None) if v else (None, "Detection returned no result")
        except Exception as e:
            return None, f"Detection failed: {e}"

    # Collect non-empty env var values
    parts = [os.environ.get(c, "") for c in rule.get("candidates", [])]
    value = " ".join(p for p in parts if p).strip()

    if field_key == "accelerators_per_node":
        nums = [int(x) for x in value.split() if x.isdigit()]
        if not nums:
            return None, f"Not captured: none of {rule['candidates']} env vars set"
        return sum(nums), None

    if field_key == "accelerator_memory_capacity":
        if not value:
            return None, f"Not captured: none of {rule['candidates']} env vars set"
        raw = value.split()[0]
        try:
            value_bytes = float(raw)
        except ValueError:
            return None, f"Could not parse memory value '{raw}'"
        if value_bytes == 0:
            return None, "Accelerator memory reported as 0"
        # Report in GiB (binary) using ceil to align with GPU product marketing values.
        # CUDA global memory is slightly below the marketed GiB due to driver reservation;
        # ceil absorbs that gap so e.g. 31.37 GiB → 32 GiB (matching "32 GB" on the box).
        if value_bytes >= 1024 ** 3:
            return f"{math.ceil(value_bytes / (1024 ** 3))}GiB", None
        return f"{int(value_bytes)}GiB", None

    if field_key == "host_storage_type" and value == "No disk layout data found":
        return None, "No disk layout data found in system"

    if rule.get("type") == "int":
        if not value:
            return None, f"Not captured: none of {rule['candidates']} env vars set"
        try:
            return int(value), None
        except (ValueError, TypeError):
            return None, f"Could not parse '{value}' as integer"

    if rule.get("optional"):
        return (value if value else None), None

    if not value:
        candidates = rule.get("candidates", [])
        if candidates:
            return None, f"Not captured: none of {candidates} env vars set"
        return None, "Not captured"

    return value, None

# -------------------------------------------------------------------


def _set_field(container, key, value, note):
    """Write value into container[key]; if note is present also write container[key + '_note']."""
    container[key] = value
    if note is not None:
        container[f"{key}_note"] = note


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

            value, note = extract_value(rule, target_key)

            if target_key in ["other_hardware", "cooling", "hw_notes"]:
                container = parsed.setdefault("hardware_ensemble", {})
                _set_field(container, target_key, value, note)
            elif ensemble_type_subpart in [
                    "processor", "host_memory", "accelerator", "networking", "storage"]:
                container = parsed.setdefault(
                    "hardware_ensemble", {}).setdefault(ensemble_type_subpart, {})
                _set_field(container, target_key, value, note)
            elif target_key in ["serving_framework", "inference_backend", "driver",
                                "operating_system", "filesystem", "container_link",
                                "other_software_stack", "sw_notes"]:
                container = parsed.setdefault("software_ensemble", {})
                _set_field(container, target_key, value, note)
        except Exception as e:
            parsed[target_key] = None
            print(
                f"[WARN] Failed to extract {target_key}: {e}",
                file=sys.stderr)

    with open(output_path, "w") as f:
        json.dump(parsed, f, indent=2)

    print(f"[INFO] Parsed system info written to {output_path}")

# -------------------------------------------------------------------


if __name__ == "__main__":
    main()
