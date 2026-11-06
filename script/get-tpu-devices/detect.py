"""TPU detection for `mlcr get,tpu-devices`.

Enumerates Google TPU chips from Linux sysfs (`/sys/bus/pci/devices`), the
same approach the `tpu-info` CLI uses. Reading sysfs does not open
`/dev/vfio/*` or `/dev/accel*`, so this works while a benchmark holds the
chips and needs no libtpu/JAX import, no `sudo`, and no extra pip packages.

Writes plain `Key: Value` lines to `tmp-run.out`; `customize.py` parses that
into the `MLC_TPU_*` env vars. See info.md for the key list and formats.
"""

import glob
import os
from importlib import metadata

SYSFS_PCI = "/sys/bus/pci/devices"
GOOGLE_PCI_VENDOR_ID = "0x1ae0"

# PCI device id -> (name, HBM GiB per chip, memory type).
#
# PCI ids and HBM sizes: github.com/google/cloud-accelerator-diagnostics
#   tpu_info/tpu_info/device.py (TpuChip.from_pci_device_id).
# HBM capacity is also on cloud.google.com/tpu/docs/{v4,v5e,v5p,v6e,tpu7x}.
# Memory *type* is only published there for v4 ("HBM2"). v5e/v5p (HBM2e) and
# TPU7x (HBM3e) follow public third-party reporting and are not confirmed by
# Google docs; an empty string means "not auto-detectable, fill in manually".
#
# TPU v2/v3 (device id 0x0027, distinguished by subsystem id) are omitted.
TPU_CHIPS = {
    "0x005e": ("TPU v4", 32, "HBM2"),
    "0x0063": ("TPU v5e", 16, "HBM2e"),
    "0x0062": ("TPU v5p", 95, "HBM2e"),
    # TODO(tpu): confirm v6e (Trillium) HBM generation before filling in.
    "0x006f": ("TPU v6e", 32, ""),
    "0x0076": ("TPU7x", 192, "HBM3e"),
}

# sysfs max_link_speed ("16.0 GT/s PCIe") -> PCIe generation.
PCIE_GEN_BY_GTS = {
    "2.5": "1.0",
    "5.0": "2.0",
    "8.0": "3.0",
    "16.0": "4.0",
    "32.0": "5.0",
    "64.0": "6.0",
}


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _libtpu_version():
    for pkg in ("libtpu", "libtpu-nightly"):
        try:
            return metadata.version(pkg)
        except metadata.PackageNotFoundError:
            continue
    return ""


def _host_interconnect(dev_path):
    """Return e.g. "PCIe 4.0 x16" from sysfs link attributes, or ""."""
    speed = _read(os.path.join(dev_path, "max_link_speed")).split(" ")[0]
    width = _read(os.path.join(dev_path, "max_link_width"))
    gen = PCIE_GEN_BY_GTS.get(speed)
    if gen and width:
        return f"PCIe {gen} x{width}"
    return ""


def get_tpu_info(sysfs_pci=SYSFS_PCI):
    """Return a list of dicts, one per TPU chip.

    A chip may expose several PCI functions (TPU7x has two TensorCores per
    chip, each its own function), so functions are grouped by their base
    address ``DDDD:BB:DD`` and counted once. ``TPU Device ID`` is emitted
    first in each dict -- customize.py uses it to start a new device block.
    """
    chips = {}  # base addr -> (device id, sysfs path of lowest function)
    for dev_path in sorted(glob.glob(os.path.join(sysfs_pci, "*"))):
        if _read(os.path.join(dev_path, "vendor")) != GOOGLE_PCI_VENDOR_ID:
            continue
        device_id = _read(os.path.join(dev_path, "device"))
        if device_id not in TPU_CHIPS:
            # Other Google PCI devices (e.g. gVNIC) share the vendor id.
            continue
        base_addr = os.path.basename(dev_path).rsplit(".", 1)[0]
        chips.setdefault(base_addr, (device_id, dev_path))

    if not chips:
        raise RuntimeError(f"no Google TPU PCI devices found under {sysfs_pci}")

    libtpu_version = _libtpu_version()

    all_tpu_info = []
    for base_addr, (device_id, dev_path) in chips.items():
        name, hbm_gib, memory_type = TPU_CHIPS[device_id]
        tpu_info = {
            "TPU Device ID": base_addr,
            "TPU Name": name,
            "Memory Type": memory_type,
            "Global memory": f"{hbm_gib} GiB",
            "Host Interconnect Type": _host_interconnect(dev_path),
        }
        if libtpu_version:
            tpu_info["libtpu version"] = libtpu_version
        all_tpu_info.append(tpu_info)

    return all_tpu_info


if __name__ == "__main__":
    try:
        tpu_info_list = get_tpu_info()
    except Exception as exc:
        raise SystemExit(f"[ERROR] Failed to collect TPU info: {exc}")

    with open("tmp-run.out", "w", encoding="utf-8") as f:
        for tpu_info in tpu_info_list:
            for key, value in tpu_info.items():
                f.write(f"{key}: {value}\n")
