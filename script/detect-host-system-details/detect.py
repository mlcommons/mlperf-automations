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


_KNOWN_TRAN = {'nvme', 'sata', 'ata', 'usb', 'scsi', 'ide', 'mmc', 'fc'}


def _classify_disk(name, tran, rota, model):
    """Return storage type string for a single disk."""
    if name.startswith("nvme") or tran == "nvme":
        return "NVMe SSD"
    if rota == "0":
        return "SSD"
    if rota == "1":
        return "HDD"
    model_up = model.upper()
    if "SSD" in model_up:
        return "SSD"
    if "HDD" in model_up or any(
            x in model for x in ["ST", "WD", "HGST", "Toshiba", "Seagate"]):
        return "HDD"
    return "Other"


def detect_storage_type(system_info):
    """Returns a string like 'NVMe SSD', 'SSD', 'HDD', or combinations joined by ' + '.

    Reads either raw lsblk text (disk_layout key) or the structured disks list
    produced by get-platform-details (disks key).  Both paths handle an optional
    VENDOR column that can displace ROTA when parsing by whitespace splitting.
    """
    types_found = set()

    # Path 1: raw lsblk text (system-info-raw.json style)
    output = ""
    for dump_key, dump in system_info.items():
        if "disk_layout" in dump_key.lower():
            if isinstance(dump, dict):
                output = dump.get("output", "").strip()
            break

    if output:
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = re.split(r'\s+', line)
            if len(parts) < 3 or parts[1] != "disk":
                continue
            name = parts[0]
            rota = "unknown"
            tran = "unknown"
            for j in range(len(parts) - 1, 1, -1):
                if parts[j] in ('0', '1'):
                    rota = parts[j]
                    tran_candidate = parts[j - 1] if j - 1 > 2 else ""
                    tran = tran_candidate if tran_candidate.lower() in _KNOWN_TRAN else "unknown"
                    break
            model = " ".join(parts[3:]) if len(parts) > 3 else ""
            t = _classify_disk(name, tran, rota, model)
            if t:
                types_found.add(t)

    # Path 2: structured disks list (system-info.json style from
    # get-platform-details)
    if not types_found:
        for disk in system_info.get("disks", []):
            if not isinstance(disk, dict) or disk.get("type") != "disk":
                continue
            t = _classify_disk(
                disk.get("name", ""),
                disk.get("transport", ""),
                disk.get("rotational", ""),
                disk.get("model", ""),
            )
            if t:
                types_found.add(t)

    if not types_found:
        return "No disk layout data found"

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


_NETWORK_FSTYPES = frozenset([
    'cifs', 'smb3', 'smbfs', 'nfs', 'nfs4', 'nfs3',
    'glusterfs', 'fuse.glusterfs', 'lustre', 'davfs', 'fuse.sshfs',
])

_SKIP_FSTYPES_CAP = frozenset([
    'tmpfs', 'devtmpfs', 'overlay', 'proc', 'sysfs', 'cgroup', 'cgroup2',
    'pstore', 'securityfs', 'debugfs', 'tracefs', 'bpf', 'hugetlbfs',
    'mqueue', 'configfs', 'fusectl', 'efivarfs', 'binfmt_misc', 'squashfs',
    'iso9660', 'devpts', 'ramfs', 'rpc_pipefs', 'sunrpc', 'autofs', 'fuse',
    'udev',
])


def _parse_df_size(s):
    size_map = {
        'T': 1024**4,
        'G': 1024**3,
        'M': 1024**2,
        'K': 1024,
        'B': 1,
        '': 1}
    m = re.match(r'^(\d+(?:\.\d+)?)([TGMKB]?)$', s.strip(), re.IGNORECASE)
    if not m:
        return 0
    return int(float(m.group(1)) * size_map.get(m.group(2).upper(), 1))


def _bytes_to_str(n):
    for unit, div in [('TB', 1024**4), ('GB', 1024**3), ('MB', 1024**2)]:
        if n >= div:
            s = f"{n / div:.1f}"
            return f"{s.rstrip('0').rstrip('.')} {unit}"
    return f"{n} B"


def _local_storage_type(device):
    name = os.path.basename(device)
    try:
        r = subprocess.run(
            ['lsblk', '-n', '-o', 'ROTA,TRAN', device],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().splitlines()[0].split()
            rota = parts[0] if parts else ''
            tran = parts[1] if len(parts) > 1 else ''
            t = _classify_disk(name, tran, rota, '')
            if t != 'Other':
                return t
    except Exception:
        pass
    try:
        r = subprocess.run(
            ['lsblk', '-n', '-s', '-o', 'NAME,TYPE,ROTA,TRAN', device],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            for line in r.stdout.strip().splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'disk':
                    disk_name = parts[0]
                    rota = parts[2] if len(parts) > 2 else ''
                    tran = parts[3] if len(parts) > 3 else ''
                    t = _classify_disk(disk_name, tran, rota, '')
                    if t != 'Other':
                        return t
    except Exception:
        pass
    return 'SSD'


def detect_storage_capacity():
    """Return a storage summary string e.g. '1.8 TB NVMe SSD, 5 TB CIFS'."""
    try:
        r = subprocess.run(
            ['df', '-T', '-h', '--output=source,fstype,size,target'],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        r = None

    rows = []
    if r is not None and r.returncode == 0:
        for line in r.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 3:
                rows.append((parts[0], parts[1], parts[2]))
    else:
        try:
            r = subprocess.run(['df', '-T', '-h'],
                               capture_output=True, text=True, timeout=10)
        except Exception:
            return ''
        if not r or r.returncode != 0:
            return ''
        for line in r.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 7:
                rows.append((parts[0], parts[1], parts[2]))

    type_bytes: dict = {}
    for source, fstype, size_str in rows:
        ft = fstype.lower()
        if ft in _SKIP_FSTYPES_CAP:
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
    parts = [
        f"{_bytes_to_str(type_bytes[t])} {t}" for t in order if t in type_bytes]
    for t in sorted(type_bytes):
        if t not in order:
            parts.append(f"{_bytes_to_str(type_bytes[t])} {t}")
    return ', '.join(parts)


def detect_gpu_driver_version():
    """Return kernel GPU driver version string, e.g. 'Driver 575.57.08' or 'ROCm Driver 6.0'."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            version = r.stdout.strip().splitlines()[0].strip()
            if version:
                return f"Driver {version}"
    except Exception:
        pass

    try:
        r = subprocess.run(["rocm-smi", "--showdriverversion"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            for line in r.stdout.splitlines():
                if "driver" in line.lower() and "version" in line.lower():
                    parts = line.split(":", 1)
                    if len(parts) > 1:
                        return f"ROCm Driver {parts[1].strip()}"
    except Exception:
        pass

    return ""


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
        "MLC_HOST_DISK_CAPACITY": detect_storage_capacity(),
        "MLC_HOST_NETWORK_CARD_COUNT": detect_network_card_count(),
        "MLC_HOST_NETWORKING": detect_networking(),
        "MLC_HOST_GPU_DRIVER_VERSION": detect_gpu_driver_version(),
    }

    with open("tmp-run.out", "w") as f:
        for key, value in results.items():
            f.write(f"{key}: {value}\n")

    print("[INFO] detect-host-system-details written to tmp-run.out")


if __name__ == "__main__":
    main()
