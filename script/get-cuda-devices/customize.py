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

    # Detect GPU interconnect type (NVLink vs PCIe) from nvidia-smi topo
    try:
        topo_out = subprocess.run(
            ['nvidia-smi', 'topo', '-m'], capture_output=True, text=True).stdout
        if re.search(r'\bNV\d+\b', topo_out):
            env['MLC_CUDA_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = 'NVLink'
        elif topo_out.strip():
            env['MLC_CUDA_DEVICE_PROP_GPU_INTERCONNECT_TYPE'] = 'PCIe'
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

    return {'return': 0}
