import json
import subprocess


def _run_xpu_smi_json(args, timeout_sec=30):
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"Command timed out: {' '.join(args)}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(
            f"Command failed ({exc.returncode}): {' '.join(args)}; stderr: {stderr}"
        ) from exc

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from command: {' '.join(args)}") from exc


def _require_keys(obj, keys, context):
    missing = [key for key in keys if key not in obj]
    if missing:
        missing_str = ", ".join(missing)
        raise RuntimeError(f"Missing required fields in {context}: {missing_str}")


def get_xpu_info():
    # Keep timeout disabled for sudo path: it may legitimately wait for password input.
    xpus_json = _run_xpu_smi_json(["sudo", "xpu-smi", "discovery", "-j"], timeout_sec=None)
    xpu_devices = xpus_json.get("device_list")
    if not isinstance(xpu_devices, list):
        raise RuntimeError("xpu-smi discovery output missing list field: device_list")

    num_xpus = len(xpu_devices)
    all_xpu_info = []

    # Map device name variants
    pci_dID_name_map = {
        "Intel(R) Graphics [0xe212]": "Intel(R) Arc(TM) Pro B50 Graphics", # B50 name variant
        "Intel(R) Graphics [0xe211]": "Intel(R) Arc(TM) Pro B60 Graphics", # B60
        "Intel(R) Graphics [0xe223]": "Intel(R) Arc(TM) Pro B70 Graphics", # B70 name variant
    }

    memory_type_map = {
        # Arc Pro Series memory types based on publicly available information. xpu-smi apis not returning memory type info, so using device name to map to memory type.
        "Intel(R) Arc(TM) Pro B50 Graphics": "GDDR6",
        "Intel(R) Arc(TM) Pro B60 Graphics": "GDDR6",
        "Intel(R) Arc(TM) Pro B70 Graphics": "GDDR6",
    }
    for i in range(num_xpus):
        device_info_json = _run_xpu_smi_json(
            ["sudo", "xpu-smi", "discovery", "-d", str(i), "-j"], timeout_sec=None
        )
        _require_keys(
            device_info_json,
            [
                "pci_device_id",
                "device_name",
                "driver_version",
                "memory_physical_size_byte",
                "core_clock_rate_mhz",
                "number_of_eus",
                "number_of_threads_per_eu",
                "pcie_generation",
                "pcie_max_link_width",
                "pcie_max_bandwidth",
            ],
            f"device {i}",
        )

        device_name = device_info_json["device_name"]
        # Map device name variants
        device_name = pci_dID_name_map.get(device_name, device_name)

        memory_type = memory_type_map.get(
            device_name, "Unknown / Not in lookup table")

        xpu_info = {
            "GPU Device ID": device_info_json["pci_device_id"],
            "GPU Name": device_name,
            "XPU driver version": f"{device_info_json['driver_version']}",
            "Memory Type": memory_type,
            "Global memory": f"{round(int(device_info_json['memory_physical_size_byte']) / 1_073_741_824)} GiB",  # Convert bytes to GiB; key maps to MLC_XPU_DEVICE_PROP_GLOBAL_MEMORY
            "Max clock rate": f"{device_info_json['core_clock_rate_mhz']} MHz",
            "Number of EUs": device_info_json["number_of_eus"],
            "EU Threads per EU": device_info_json["number_of_threads_per_eu"],
            "Host Interconnect Type": f"{float(device_info_json['pcie_generation']):.1f} x{device_info_json['pcie_max_link_width']}",
            "Host Interconnect Bandwidth": f"{device_info_json['pcie_max_bandwidth']}",
        }

        all_xpu_info.append(xpu_info)

    return all_xpu_info


# Print the XPU information for all available XPUs
if __name__ == "__main__":
    try:
        xpu_info_list = get_xpu_info()
    except Exception as exc:
        raise SystemExit(f"[ERROR] Failed to collect XPU info: {exc}")

    with open("tmp-run.out", "w", encoding="utf-8") as f:
        for xpu_info in xpu_info_list:
            for key, value in xpu_info.items():
                f.write(f"{key}: {value}\n")
