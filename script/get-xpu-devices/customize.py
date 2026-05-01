from mlc import utils
from utils import *
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

            key_env = 'MLC_XPU_DEVICE_PROP_' + key.upper().replace(' ', '_')
            # Host Interconnect Type
            if key_env == 'MLC_XPU_DEVICE_PROP_HOST_INTERCONNECT_TYPE':
                if val and not val.startswith('PCIe'):
                    val = 'PCIe ' + val

            env[key_env] = val

    state['mlc_xpu_num_devices'] = gpu_id + 1
    env['MLC_XPU_NUM_DEVICES'] = gpu_id + 1

    state['mlc_xpu_device_prop'] = p
    state['mlc_xpu_devices_prop'] = gpu

    # GPU Interconnect Type
    try:
        topo_out = subprocess.run(
            ['xpu-smi', 'topology', '-m'], capture_output=True, text=True).stdout
        if re.search(r'\bXL\d+\b', topo_out):
            env['MLC_XPU_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = 'XeLink'
        elif re.search(r'\bXL*\d+\b', topo_out):
            env['MLC_XPU_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = 'XeLink + MDF'
        elif topo_out.strip():
            env['MLC_XPU_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = ''
    except Exception:
        pass
    return {'return': 0}
