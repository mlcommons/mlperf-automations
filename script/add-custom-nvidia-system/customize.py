from mlc import utils
from utils import *
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH']

    if is_true(env.get('MLC_CUSTOM_CONFIG', '')):
        state = i['state']
        system_meta = state['MLC_SUT_META']
        with open(os.path.join(env['MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH'], "systems", f"{env.get('MLC_NVIDIA_SYSTEM_NAME')}.json"), "w") as fp:
            json.dump(system_meta, fp, indent=2)

    return {'return': 0}
