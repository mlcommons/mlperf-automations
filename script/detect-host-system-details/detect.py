import json
import re
import os
import subprocess
import sys
import argparse
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(
        description="Detect host system details from platform-details JSON and /sys filesystem."
    )
    p.add_argument("--input", required=True,
                   help="Path to MLC_PLATFORM_DETAILS_FILE_PATH JSON file")
    return p.parse_args()


def get_link_layer(device_name):
    """Returns 'InfiniBand' or 'Ethernet' for a given RDMA device, or None."""
    path = f"/sys/class/infiniband/{device_name}/ports/1/link_layer"
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return f.read().strip()


def detect_memory_configuration(system_info):
    """Parses dmidecode output to produce a DIMM configuration string.
    First tries the pre-collected dmidecode_full entry from the platform-details JSON.
    Falls back to running dmidecode directly via MLC_SUDO if the JSON entry is absent or failed.
    Returns a string like '16 x 64GB DDR5-4800' or ''.
    """
    dmidecode_output = ""
    for dump_key, dump in system_info.items():
        if "dmidecode_full" in dump_key:
            val = dump.get("output", "")
            if val and "sudo not available" not in val and not val.startswith(
                    "FAILED"):
                dmidecode_output = val
            break

    if not dmidecode_output:
        sudo = os.environ.get('MLC_SUDO', '').strip()
        cmd = ['sudo', 'dmidecode'] if sudo == 'sudo' else ['dmidecode']
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                dmidecode_output = result.stdout
        except Exception:
            pass

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

        size_match = re.search(r"Size:\s+(\d+)\s+GB", block, re.IGNORECASE)
        type_match = re.search(r"Type:\s+(DDR\d+)", block, re.IGNORECASE)
        speed_match = re.search(
            r"(Configured Clock Speed|Speed):\s+(\d+)\s+MT/s", block, re.IGNORECASE
        )

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
    return f"{dimm_count} x {dimm_size}GB {dimm_type}-{dimm_speed}".rstrip("-")


def detect_storage_type(system_info):
    """Parses disk_layout (lsblk output) from system_info JSON.
    Returns a string like 'NVMe SSD', 'SSD', 'HDD', or combinations joined by ' + '.
    """
    output = ""
    for dump_key, dump in system_info.items():
        if "disk_layout" in dump_key.lower():
            output = dump.get("output", "").strip()
            break

    if not output:
        return "No disk layout data found"

    types_found = set()

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = re.split(r'\s+', line)

        if len(parts) < 5:
            continue

        name = parts[0]
        dev_type = parts[1]
        tran = parts[-2] if len(parts) >= 6 else "unknown"
        rota = parts[-1] if len(parts) >= 6 else "unknown"

        if dev_type != "disk":
            continue

        if name.startswith("nvme") or tran == "nvme":
            types_found.add("NVMe SSD")
        elif rota == "0":
            types_found.add("SSD")
        elif rota == "1":
            types_found.add("HDD")
        else:
            model_start = 3
            model_end = len(parts) - 2
            model = " ".join(parts[model_start:model_end]
                             ) if model_end > model_start else ""
            if "SSD" in model.upper():
                types_found.add("SSD")
            elif "HDD" in model.upper() or any(
                x in model for x in ["ST", "WD", "HGST", "Toshiba", "Seagate"]
            ):
                types_found.add("HDD")
            else:
                types_found.add("Other")

    if not types_found:
        return "No physical disks detected"

    ordered = []
    for t in ["NVMe SSD", "SSD", "HDD", "Other"]:
        if t in types_found:
            ordered.append(t)
    return " + ".join(ordered)


def detect_network_card_count():
    """Scans /sys/class/net for physical (non-virtual, non-loopback) NICs.
    Returns count as a string.
    """
    net_dir = "/sys/class/net"
    if not os.path.isdir(net_dir):
        return "0"

    count = 0
    for ifname in os.listdir(net_dir):
        if ifname == "lo":
            continue
        device_link = f"{net_dir}/{ifname}/device"
        if os.path.islink(device_link):
            target = os.readlink(device_link)
            if "/virtual/" not in target:
                count += 1
    return str(count)


def detect_networking():
    """Scans /sys/class/infiniband for RDMA devices.
    Returns 'Ethernet' if no IB devices found, otherwise per-device InfiniBand/RoCE strings.
    """
    ib_dir = "/sys/class/infiniband"
    if not os.path.isdir(ib_dir):
        return "Ethernet"

    devices = os.listdir(ib_dir)
    if not devices:
        return "Ethernet"

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


def main():
    args = parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(
            f"[WARN] Platform details file not found: {input_path}",
            file=sys.stderr)
        system_info = {}
    else:
        with open(input_path) as f:
            system_info = json.load(f)

    results = {
        "MLC_HOST_MEMORY_CONFIGURATION": detect_memory_configuration(system_info),
        "MLC_HOST_STORAGE_TYPE": detect_storage_type(system_info),
        "MLC_HOST_NETWORK_CARD_COUNT": detect_network_card_count(),
        "MLC_HOST_NETWORKING": detect_networking(),
    }

    with open("tmp-run.out", "w") as f:
        for key, value in results.items():
            f.write(f"{key}: {value}\n")

    print("[INFO] detect-host-system-details written to tmp-run.out")


if __name__ == "__main__":
    main()
