from mlc import utils
from utils import *
import os
import re
import subprocess


def preprocess(i):

    env = i['env']

    if str(env.get('MLC_DETECT_USING_PYCUDA', '')
           ).lower() in ["1", "yes", "true"]:
        i['run_script_input']['script_name'] = 'detect'

    return {'return': 0}


def _topo_data_rows(topo_out):
    """Return the per-GPU rows of nvidia-smi topo -m output, header excluded."""
    data_rows = []
    for line in topo_out.split('\n'):
        line = line.strip()
        if not re.match(r'GPU\d+\s', line):
            continue
        parts = line.split()
        # Skip the header row whose second column is also a GPU/NIC label.
        if len(parts) >= 2 and re.match(r'(GPU|NIC)\d+', parts[1]):
            continue
        data_rows.append(parts)
    return data_rows


def _derive_topology_desc(topo_out, n_gpus):
    """Return 'Mesh', 'Direct', or None from nvidia-smi topo -m output.

    Mesh   = all GPU pairs connected via NVLink (fully connected).
    Direct = PCIe-only or partial NVLink connections.
    None   = single GPU (no inter-GPU topology to describe).
    """
    if n_gpus <= 1:
        return None
    data_rows = _topo_data_rows(topo_out)
    if len(data_rows) < n_gpus:
        return None
    nv_pairs = 0
    total_pairs = n_gpus * (n_gpus - 1)
    for parts in data_rows[:n_gpus]:
        for c in parts[1:n_gpus + 1]:
            if re.match(r'NV\d+', c):
                nv_pairs += 1
    return 'Mesh' if nv_pairs == total_pairs else 'Direct'


def _derive_per_gpu_interconnect(topo_out):
    """Return ['NVLink' | 'PCIe', ...], one entry per nvidia-smi GPU index.

    A host can hold accelerators on different fabrics — NVLinked accelerators
    beside a PCIe-only one — so the fabric is read per GPU rather than once for
    the whole host. Sized from the topo matrix itself rather than the CUDA
    device count, which is smaller whenever CUDA_VISIBLE_DEVICES hides GPUs."""
    data_rows = _topo_data_rows(topo_out)
    n = len(data_rows)
    return ['NVLink' if any(re.match(r'NV\d+', c) for c in parts[1:n + 1])
            else 'PCIe' for parts in data_rows]


def _parse_smi_query(smi_out):
    """Return [(product name, 'PCIe GenX xY' or ''), ...] per nvidia-smi index.

    Parsed out of the `nvidia-smi -q` output this script already collects for
    MLC_CUDA_DEVICE_PROP_HOST_INTERCONNECT_TYPE, so no extra nvidia-smi call is
    needed. Blocks are emitted in PCI bus id order, matching the row order of
    `nvidia-smi topo -m`."""
    gpus = []
    for block in re.split(r'\n(?=GPU [0-9A-Fa-f]{8}:)', smi_out):
        name = re.search(r'Product Name\s*:\s*(.+)', block)
        if not name:
            continue
        gen = re.search(
            r'PCIe Generation\s*\n\s*Max\s*:\s*\d+\s*\n\s*Current\s*:\s*(\d+)',
            block)
        width = re.search(
            r'Link Width\s*\n\s*Max\s*:\s*\d+x\s*\n\s*Current\s*:\s*(\d+)x',
            block)
        gpus.append((
            name.group(1).strip(),
            f'PCIe Gen{gen.group(1)} x{width.group(1)}'
            if gen and width else ''))
    return gpus


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    r = utils.load_txt(file_name='tmp-run.out',
                       check_if_exists=True,
                       split=True)
    if r['return'] > 0:
        return r

    lst = r['list']

    # properties
    p = {}
    gpu = {}

    gpu_id = -1

    for line in lst:
        # print (line)

        j = line.find(':')

        if j >= 0:
            key = line[:j].strip()
            val = line[j + 1:].strip()

            if key == "GPU Device ID":
                gpu_id += 1
                gpu[gpu_id] = {}

            if gpu_id < 0:
                continue

            gpu[gpu_id][key] = val
            p[key] = val

            key_env = 'MLC_CUDA_DEVICE_PROP_' + key.upper().replace(' ', '_')
            env[key_env] = val

    state['mlc_cuda_num_devices'] = gpu_id + 1
    env['MLC_CUDA_NUM_DEVICES'] = gpu_id + 1

    state['mlc_cuda_device_prop'] = p
    state['mlc_cuda_devices_prop'] = gpu

    # Detect host interconnect (PCIe gen/width) from nvidia-smi -q. The same
    # output is reused below for the per-device values, so nvidia-smi is
    # queried no more times than before.
    smi_gpus = []
    try:
        smi_out = subprocess.run(
            ['nvidia-smi', '-q'], capture_output=True, text=True).stdout
        smi_gpus = _parse_smi_query(smi_out)
        gen = re.search(
            r'PCIe Generation\s*\n\s*Max\s*:\s*\d+\s*\n\s*Current\s*:\s*(\d+)', smi_out)
        width = re.search(
            r'Link Width\s*\n\s*Max\s*:\s*\d+x\s*\n\s*Current\s*:\s*(\d+)x', smi_out)
        if gen and width:
            env['MLC_CUDA_DEVICE_PROP_HOST_INTERCONNECT_TYPE'] = \
                f'PCIe Gen{gen.group(1)} x{width.group(1)}'
        elif smi_out.strip():
            env['MLC_CUDA_DEVICE_PROP_HOST_INTERCONNECT_TYPE'] = 'PCIe'
    except Exception:
        pass

    # Detect GPU interconnect type (NVLink vs PCIe) from nvidia-smi topo
    per_gpu_fabric = []
    try:
        topo_out = subprocess.run(
            ['nvidia-smi', 'topo', '-m'], capture_output=True, text=True).stdout
        if re.search(r'\bNV\d+\b', topo_out):
            env['MLC_CUDA_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = 'NVLink'
        elif topo_out.strip():
            env['MLC_CUDA_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = 'PCIe'
        if topo_out.strip():
            clean_topo = re.sub(r'\x1b\[[0-9;]*m', '', topo_out).strip()
            env['MLC_CUDA_DEVICE_PROP_GPU_TOPOLOGY'] = clean_topo
            topo_desc = _derive_topology_desc(clean_topo, gpu_id + 1)
            if topo_desc:
                env['MLC_CUDA_DEVICE_PROP_GPU_TOPOLOGY_DESC'] = topo_desc
            per_gpu_fabric = _derive_per_gpu_interconnect(clean_topo)
    except Exception:
        pass

    # Record the interconnect alongside the other 19 properties of each device,
    # so state['mlc_cuda_devices_prop'] describes every device completely and a
    # consumer needs no second source. The scalar env vars above still carry
    # the host-wide value for the scripts that read them.
    #
    # nvidia-smi enumerates by PCI bus id while CUDA may reorder devices, so
    # the two are joined on product name rather than on index.
    fabric_by_model, host_link_by_model = {}, {}
    for idx, (smi_name, host_link) in enumerate(smi_gpus):
        if idx < len(per_gpu_fabric):
            fabric_by_model.setdefault(smi_name, per_gpu_fabric[idx])
        if host_link:
            host_link_by_model.setdefault(smi_name, host_link)

    for device_id in gpu:
        model_name = str(gpu[device_id].get('GPU Name', '')).strip()
        gpu[device_id]['GPU interconnect'] = fabric_by_model.get(
            model_name, env.get('MLC_CUDA_DEVICE_PROP_GPU_INTERCONNECT_TYPE', ''))
        gpu[device_id]['Host interconnect'] = host_link_by_model.get(
            model_name, env.get('MLC_CUDA_DEVICE_PROP_HOST_INTERCONNECT_TYPE', ''))

    return {'return': 0}
