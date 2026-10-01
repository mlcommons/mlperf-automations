"""Detect the Cloud TPU chips attached to this host.

TPUs have no vendor SMI tool, so this pieces the answer together from what a
TPU VM exposes, most reliable first:

- chip count: the device nodes (/dev/accel* on v2-v4, /dev/vfio/<group> on
  v5e and later), falling back to what JAX reports;
- generation: TPU_ACCELERATOR_TYPE, then the GCE metadata server, then JAX's
  device_kind;
- per-chip HBM and memory type: a lookup table of published figures, falling
  back to JAX's memory_stats() for a generation not in the table;
- host interconnect: the PCIe link of each chip, read from sysfs.

The JAX probe is optional (stdlib only otherwise) and runs in a subprocess
with a timeout, because initialising a TPU that another process holds (a
notebook kernel that already imported jax, for instance) can hang or fail.
"""

import glob
import importlib.metadata
import json
import os
import re
import subprocess
import sys
import urllib.request

# name, HBM per chip in GiB, memory type, JAX devices per chip, ICI torus
# dimensions. v2 and v3 expose each of a chip's two TensorCores as its own JAX
# device; v4 and v5p fuse theirs into one megacore device.
#
# Capacity and memory type are only what Google's Cloud TPU spec pages
# (docs.cloud.google.com/tpu/docs/<gen>) state. Only v4's names an HBM
# generation, so the rest say "HBM". v2's page gives no per-chip figures, so
# its capacity (0) comes from JAX instead.
GENERATIONS = {
    "v2": ("TPU v2", 0, "HBM", 2, 2),
    "v3": ("TPU v3", 32, "HBM", 2, 2),
    "v4": ("TPU v4", 32, "HBM2", 1, 3),
    "v5e": ("TPU v5e", 16, "HBM", 1, 2),
    "v5p": ("TPU v5p", 95, "HBM", 1, 3),
    "v6e": ("TPU v6e", 32, "HBM", 1, 2),
}

# Accelerator-type prefixes (e.g. "v5litepod-8") to a GENERATIONS key.
_ACCEL_TYPE_PREFIXES = [
    ("v5litepod", "v5e"),
    ("v5e", "v5e"),
    ("v5p", "v5p"),
    ("v6e", "v6e"),
    ("v4", "v4"),
    ("v3", "v3"),
    ("v2", "v2"),
]

_METADATA_URL = ("http://metadata.google.internal/computeMetadata/v1/"
                 "instance/attributes/accelerator-type")

_GOOGLE_PCI_VENDOR = "0x1ae0"

_PCIE_GEN = {"2.5": 1, "5.0": 2, "8.0": 3, "16.0": 4, "32.0": 5, "64.0": 6}

_JAX_PROBE = """
import json, jax
devices = jax.local_devices()
out = {"platform": devices[0].platform, "count": len(devices),
       "kind": devices[0].device_kind}
try:
    out["bytes_limit"] = (devices[0].memory_stats() or {}).get("bytes_limit")
except Exception:
    pass
try:
    out["coords"] = [list(d.coords) for d in devices]
except Exception:
    pass
print(json.dumps(out))
"""


def _log(msg):
    print(f"[get-tpu-devices] {msg}", file=sys.stderr)


def accelerator_type():
    """The slice's accelerator type, e.g. "v5litepod-8", or ""."""
    value = os.environ.get("TPU_ACCELERATOR_TYPE", "").strip()
    if value:
        return value, "TPU_ACCELERATOR_TYPE"
    if os.environ.get("TPU_SKIP_MDS_QUERY") == "1":
        # Set where the metadata server is not the TPU's (Colab answers 404).
        return "", ""
    try:
        req = urllib.request.Request(
            _METADATA_URL, headers={"Metadata-Flavor": "Google"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            value = resp.read().decode().strip()
        if value:
            return value, "GCE metadata"
    except Exception as exc:
        _log(f"metadata server not available: {exc}")
    return "", ""


def generation_from_accel_type(accel_type):
    lowered = accel_type.lower()
    for prefix, gen in _ACCEL_TYPE_PREFIXES:
        if lowered.startswith(prefix):
            return gen
    return ""


def generation_from_device_kind(kind):
    """JAX device_kind ("TPU v5 lite", "TPU v4") to a GENERATIONS key."""
    m = re.search(r"v(\d+)\s*(lite|e|p)?", kind.lower())
    if not m:
        return ""
    major, suffix = m.group(1), m.group(2) or ""
    if major in ("5", "6"):
        # v5 is v5p unless it says lite; v6 has only shipped as v6e.
        suffix = "e" if suffix in ("lite", "e") or major == "6" else "p"
        return f"v{major}{suffix}"
    return f"v{major}"


def chip_pci_dirs():
    """One sysfs PCI device directory per TPU chip, and which nodes found them."""
    accel = sorted(glob.glob("/dev/accel[0-9]*"),
                   key=lambda p: int(re.sub(r"\D", "", p) or 0))
    if accel:
        dirs = [os.path.realpath(f"/sys/class/accel/{os.path.basename(p)}/device")
                for p in accel]
        return dirs, "/dev/accel*"

    # A VFIO group can hold any passed-through device, so keep only the
    # groups whose device is a Google processing accelerator.
    groups = sorted((g for g in os.listdir("/dev/vfio") if g.isdigit()),
                    key=int) if os.path.isdir("/dev/vfio") else []
    dirs = []
    for g in groups:
        for member in sorted(
                glob.glob(f"/sys/kernel/iommu_groups/{g}/devices/*")):
            if is_tpu_pci(member):
                dirs.append(os.path.realpath(member))
                break
    if dirs:
        return dirs, "/dev/vfio"

    return [], ""


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def is_tpu_pci(pci_dir):
    """Google's PCI vendor ID with the processing-accelerator class (0x12)."""
    return (_read(os.path.join(pci_dir, "vendor")) == _GOOGLE_PCI_VENDOR
            and _read(os.path.join(pci_dir, "class")).startswith("0x12"))


def pcie_link(pci_dir):
    """e.g. "PCIe Gen4 x16", or "" when sysfs does not say."""
    if not pci_dir:
        return ""
    # A VM's virtual PCIe root often reports the current link as "Unknown"
    # and x0, so fall back to the device's maximum link. A Colab v6e reports
    # both as Unknown (max width 255), leaving the field for the submitter.
    for prefix in ("current", "max"):
        speed = _read(os.path.join(pci_dir, f"{prefix}_link_speed"))
        width = _read(os.path.join(pci_dir, f"{prefix}_link_width"))
        m = re.match(r"([\d.]+)\s*GT/s", speed)
        if m:
            break
    else:
        return ""
    # 0 and 255 are what a link with no negotiated width reports.
    if not width.isdigit() or width in ("0", "255"):
        width = ""
    gen = _PCIE_GEN.get(f"{float(m.group(1)):.1f}")
    label = f"PCIe Gen{gen}" if gen else f"PCIe {speed}"
    return f"{label} x{width}" if width else label


def jax_probe():
    if os.environ.get("MLC_TPU_SKIP_JAX_PROBE",
                      "").lower() in ("1", "true", "yes"):
        return {}
    try:
        timeout = int(os.environ.get("MLC_TPU_JAX_PROBE_TIMEOUT", "120"))
        r = subprocess.run([sys.executable, "-c", _JAX_PROBE],
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        _log("JAX probe timed out; is the TPU held by another process?")
        return {}
    except OSError as exc:
        _log(f"JAX probe could not start: {exc}")
        return {}
    if r.returncode != 0:
        last = (r.stderr.strip().splitlines() or ["no output"])[-1]
        _log(f"JAX probe failed: {last}")
        return {}
    try:
        info = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {}
    if info.get("platform") != "tpu":
        _log(f"JAX sees platform {info.get('platform')!r}, not tpu")
        return {}
    return info


def _bounds(var):
    try:
        return [int(x) for x in os.environ.get(var, "").split(",")]
    except ValueError:
        return []


def ici_topology(num_chips, coords, dims):
    """The slice's ICI shape, e.g. "16x16" or "4x4x4", in Google's format.

    A host holding its full complement of chips is part of a slice shaped
    TPU_HOST_BOUNDS x TPU_CHIPS_PER_HOST_BOUNDS. A host with fewer (a v6e-1,
    say, where the bounds still describe a four-chip host) is the whole
    slice, so its own chips' coordinates give the shape.
    """
    per_host = _bounds("TPU_CHIPS_PER_HOST_BOUNDS")
    hosts = _bounds("TPU_HOST_BOUNDS")
    shape = []
    if len(per_host) == 3 and len(hosts) == 3 \
            and num_chips == per_host[0] * per_host[1] * per_host[2]:
        shape = [h * c for h, c in zip(hosts, per_host)]
    elif coords and all(len(c) == 3 for c in coords):
        shape = [max(axis) - min(axis) + 1 for axis in zip(*coords)]
    if not shape:
        return ""
    return "x".join(str(n) for n in shape[:dims or 3])


def libtpu_version():
    for pkg in ("libtpu", "libtpu-nightly"):
        try:
            return importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            continue
    return ""


def get_tpu_info():
    accel_type, type_source = accelerator_type()
    pci_dirs, node_source = chip_pci_dirs()
    jax = jax_probe()

    gen = generation_from_accel_type(accel_type) if accel_type else ""
    if not gen and jax.get("kind"):
        gen = generation_from_device_kind(jax["kind"])
        type_source = type_source or "JAX device_kind"
    known = GENERATIONS.get(gen)

    num_chips = len(pci_dirs)
    count_source = node_source
    if not num_chips and jax.get("count"):
        num_chips = jax["count"] // (known[3] if known else 1)
        count_source = "JAX local_devices"
    if not num_chips:
        hint = ""
        if os.environ.get("COLAB_TPU_ADDR"):
            hint = (" COLAB_TPU_ADDR is set, so this looks like the legacy Colab "
                    "TPU Node runtime, where the TPU is remote and not attached "
                    "to this host.")
        raise RuntimeError("no TPU chips found: no /dev/accel* or /dev/vfio "
                           "device nodes, and JAX found no TPU." + hint)

    if known:
        name, hbm_gib, mem_type, _, dims = known
    else:
        name = jax.get("kind") or accel_type or "TPU (unknown generation)"
        hbm_gib, mem_type, dims = 0, "", 0
    if not hbm_gib and jax.get("bytes_limit"):
        cores = 1
        if jax.get("count") and jax["count"] > num_chips:
            cores = jax["count"] // num_chips
        # bytes_limit is per JAX device and a little under the physical
        # HBM; parse.py rounds GiB up, which absorbs the gap.
        hbm_gib = jax["bytes_limit"] * cores / 1024 ** 3

    topology = ici_topology(num_chips, jax.get("coords"), dims)

    chips = []
    for i in range(num_chips):
        pci_dir = pci_dirs[i] if i < len(pci_dirs) else ""
        chips.append({
            "TPU Device ID": i,
            "TPU Name": name,
            "Accelerator Type": accel_type,
            "PCI Address": os.path.basename(pci_dir),
            "Global memory in GiB": f"{hbm_gib:g}" if hbm_gib else "",
            "Memory Type": mem_type,
            "TPU Interconnect Type": "ICI",
            "TPU Topology Desc": topology,
            "Host Interconnect Type": pcie_link(pci_dir),
            "libtpu Version": libtpu_version(),
            "Detection Source": f"count={count_source}; "
                                f"type={type_source or 'none'}; "
                                f"jax={'yes' if jax else 'no'}",
        })
    return chips


if __name__ == "__main__":
    try:
        chips = get_tpu_info()
    except Exception as exc:
        raise SystemExit(f"[ERROR] Failed to collect TPU info: {exc}")

    for chip in chips:
        for key, value in chip.items():
            print(f"{key}: {value}")
