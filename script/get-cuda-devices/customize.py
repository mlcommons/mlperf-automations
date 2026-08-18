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


# CUDA device properties reported per accelerator model, with the env var
# suffix used for the joined per-model value.
_PER_MODEL_PROPS = [
    ("GPU Name", "GPU_NAME"),
    ("Global memory", "GLOBAL_MEMORY"),
    ("Memory Type", "MEMORY_TYPE"),
    ("Max clock rate", "MAX_CLOCK_RATE"),
]


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


def _derive_per_gpu_interconnect(topo_out, n_gpus):
    """Return ['NVLink' | 'PCIe', ...], one entry per nvidia-smi GPU index.

    A host can hold accelerators on different fabrics — NVLinked accelerators
    beside a PCIe-only one — so the fabric is read per GPU rather than once for
    the whole host."""
    data_rows = _topo_data_rows(topo_out)
    if len(data_rows) < n_gpus:
        return []
    per_gpu = []
    for parts in data_rows[:n_gpus]:
        cells = parts[1:n_gpus + 1]
        per_gpu.append(
            'NVLink' if any(re.match(r'NV\d+', c) for c in cells) else 'PCIe')
    return per_gpu


def _query_nvidia_smi_gpus():
    """Return (names by nvidia-smi index, {gpu name: host interconnect}).

    The host interconnect is keyed by product name, not index: nvidia-smi
    enumerates by PCI bus id while CUDA may reorder devices, so joining the two
    on index would mismatch on a host with more than one accelerator model."""
    try:
        out = subprocess.run(
            ['nvidia-smi',
             '--query-gpu=index,name,pcie.link.gen.current,pcie.link.width.current',
             '--format=csv,noheader'],
            capture_output=True, text=True).stdout
    except Exception:
        return [], {}
    names, host_interconnect = [], {}
    for line in out.strip().split('\n'):
        parts = [c.strip() for c in line.split(',')]
        if len(parts) < 2 or not parts[1]:
            continue
        names.append(parts[1])
        if len(parts) >= 4 and parts[2].isdigit() and parts[3].isdigit():
            host_interconnect.setdefault(
                parts[1], f'PCIe Gen{parts[2]} x{parts[3]}')
    return names, host_interconnect


def _join_per_model(models, value_by_model):
    """Join one value per model, in the order the models were first seen.

    Returns '' when no model has a value, so the caller can leave the env var
    unset rather than publishing a list of blanks."""
    values = [str(value_by_model.get(m, '') or '').strip() for m in models]
    return ", ".join(values) if any(values) else ""


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

    # Group the walked devices by accelerator model. The MLC_CUDA_DEVICE_PROP_*
    # vars above hold whichever device was enumerated last, which is all a
    # single-model host needs but loses every other model on a mixed host. The
    # _PER_MODEL vars below carry one value per model instead, in the order the
    # models were first seen, so a consumer can describe each of them.
    models = []
    model_prop = {}
    model_count = {}
    for device_id in sorted(gpu):
        model_name = str(gpu[device_id].get('GPU Name', '')).strip()
        if not model_name:
            continue
        if model_name not in model_prop:
            models.append(model_name)
            model_prop[model_name] = gpu[device_id]
            model_count[model_name] = 0
        model_count[model_name] += 1

    smi_names, smi_host_interconnect = _query_nvidia_smi_gpus()

    # Detect GPU interconnect type (NVLink vs PCIe) from nvidia-smi topo
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
            per_gpu = _derive_per_gpu_interconnect(clean_topo, gpu_id + 1)
            if per_gpu and smi_names:
                by_model = {}
                for smi_name, interconnect in zip(smi_names, per_gpu):
                    by_model.setdefault(smi_name, interconnect)
                model_interconnect = _join_per_model(models, by_model)
                if model_interconnect:
                    env['MLC_CUDA_DEVICE_PROP_GPU_INTERCONNECT_TYPE_PER_MODEL'] = \
                        model_interconnect
    except Exception:
        pass

    # Detect host interconnect (PCIe gen/width) from nvidia-smi -q
    try:
        smi_out = subprocess.run(
            ['nvidia-smi', '-q'], capture_output=True, text=True).stdout
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

    if models:
        env['MLC_CUDA_DEVICE_MODEL_COUNT'] = len(models)
        env['MLC_CUDA_DEVICE_COUNT_PER_MODEL'] = ", ".join(
            str(model_count[m]) for m in models)
        for prop_key, suffix in _PER_MODEL_PROPS:
            joined = _join_per_model(
                models, {m: model_prop[m].get(prop_key, '') for m in models})
            if joined:
                env[f'MLC_CUDA_DEVICE_PROP_{suffix}_PER_MODEL'] = joined
        host_interconnect = _join_per_model(models, smi_host_interconnect)
        if host_interconnect:
            env['MLC_CUDA_DEVICE_PROP_HOST_INTERCONNECT_TYPE_PER_MODEL'] = \
                host_interconnect
        state['mlc_cuda_devices_prop_per_model'] = [
            {'model': m, 'count': model_count[m], 'prop': model_prop[m]}
            for m in models]

    return {'return': 0}
