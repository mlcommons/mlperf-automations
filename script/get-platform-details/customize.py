from mlc import utils
import os
import subprocess


def check_installation(command, os_info):
    if os_info['platform'] == "windows":
        return subprocess.call(
            [command, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) == 0
    elif os_info['platform'] == "linux":
        return subprocess.call(['which', command], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE) == 0  # 0 means the package is there


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    if not check_installation("numactl", os_info):
        env['MLC_INSTALL_NUMACTL'] = 'True'

    # if not check_installation("cpupower",os_info):
    env['MLC_INSTALL_CPUPOWER'] = 'True'

    if env.get('MLC_PLATFORM_DETAILS_FILE_PATH', '') == '':
        if env.get('MLC_PLATFORM_DETAILS_DIR_PATH', '') == '':
            env['MLC_PLATFORM_DETAILS_DIR_PATH'] = os.getcwd()
        if env.get('MLC_PLATFORM_DETAILS_FILE_NAME', '') == '':
            env['MLC_PLATFORM_DETAILS_FILE_NAME'] = "system-info.json"
        env['MLC_PLATFORM_DETAILS_FILE_PATH'] = os.path.join(
            env['MLC_PLATFORM_DETAILS_DIR_PATH'], env['MLC_PLATFORM_DETAILS_FILE_NAME'])

    return {'return': 0}


def postprocess(i):

    state = i['state']

    env = i['env']

    os_info = i['os_info']

    automation = i['automation']

    import json

    json_path = env['MLC_PLATFORM_DETAILS_FILE_PATH']
    if os.path.isfile(json_path):
        with open(json_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}

    if env.get('MLC_ACCELERATOR_BACKEND', '') == 'cuda':
        data['accelerator_model_name'] = env.get('MLC_CUDA_DEVICE_PROP_GPU_NAME', '')
        data['accelerators_per_node'] = int(env.get('MLC_CUDA_NUM_DEVICES', 0))

        if 'MLC_CUDA_DEVICE_PROP_GLOBAL_MEMORY' in env:
            data['accelerator_memory_capacity'] = int(env['MLC_CUDA_DEVICE_PROP_GLOBAL_MEMORY'])

        data['accelerator_memory_type'] = env.get('MLC_ACCELERATOR_MEMORY_TYPE', '')
        data['accelerator_host_interconnect'] = env.get('MLC_ACCELERATOR_HOST_INTERCONNECT', '')
        data['accelerator_interconnect'] = env.get('MLC_ACCELERATOR_INTERCONNECT', '')
    
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    return {'return': 0}
