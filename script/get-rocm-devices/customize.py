from mlc import utils
import os
import subprocess
from utils import *

def preprocess(i):

    env = i['env']

    if is_true(str(env.get('MLC_DETECT_USING_HIP-PYTHON', ''))):
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

            key_env = 'MLC_ROMLC_DEVICE_PROP_' + key.upper().replace(' ', '_')
            env[key_env] = val

    state['mlc_romlc_num_devices'] = gpu_id + 1
    env['MLC_ROMLC_NUM_DEVICES'] = gpu_id + 1

    state['mlc_romlc_device_prop'] = p
    state['mlc_romlc_devices_prop'] = gpu

    return {'return': 0}
