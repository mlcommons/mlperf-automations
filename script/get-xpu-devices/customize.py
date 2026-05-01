from mlc import utils
import os
import re
import subprocess


def preprocess(i):
    env = i['env']
    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    tmp_run_out = os.path.join(env.get('MLC_TMP_CURRENT_PATH', '.'), 'tmp-run.out')

    r = utils.load_txt(file_name=tmp_run_out,
                       check_if_exists=True,
                       split=True)
    if r['return'] > 0:
        return r

    lst = r['list']

    # properties
    p = {}
    gpu = {}
    allowed_keys = {
        "GPU Device ID",
        "GPU Name",
        "XPU driver version",
        "Memory Type",
        "Global memory",
        "Max clock rate",
        "Number of EUs",
        "EU Threads per EU",
        "Host Interconnect Type",
        "Host Interconnect Bandwidth",
    }

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

            if key not in allowed_keys:
                continue

            gpu[gpu_id][key] = val
            p[key] = val

            key_env = 'MLC_XPU_DEVICE_PROP_' + key.upper().replace(' ', '_')
            # Host Interconnect Type
            if key_env == 'MLC_XPU_DEVICE_PROP_HOST_INTERCONNECT_TYPE':
                if val and not val.startswith('PCIe'):
                    val = 'PCIe ' + val

            env[key_env] = val

    if gpu_id < 0:
        return {'return': 1, 'error': 'No GPU Device ID entries found in tmp-run.out'}

    state['mlc_xpu_num_devices'] = gpu_id + 1
    env['MLC_XPU_NUM_DEVICES'] = gpu_id + 1

    state['mlc_xpu_device_prop'] = p
    state['mlc_xpu_devices_prop'] = gpu

    # GPU Interconnect Type
    try:
        topo_out = subprocess.run(
            ['xpu-smi', 'topology', '-m'], capture_output=True, text=True, timeout=10
        ).stdout
        if re.search(r'\bXL\d+\b', topo_out):
            env['MLC_XPU_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = 'XeLink'
        elif re.search(r'\bXL*\d+\b', topo_out):
            env['MLC_XPU_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = 'XeLink + MDF'
        elif topo_out.strip():
            env['MLC_XPU_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = ''
    except subprocess.TimeoutExpired:
        # Topology probing is optional; keep script successful if command hangs.
        env['MLC_XPU_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = ''
    except Exception:
        # Topology probing is best-effort and should not fail device enumeration.
        env['MLC_XPU_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = ''
    return {'return': 0}
