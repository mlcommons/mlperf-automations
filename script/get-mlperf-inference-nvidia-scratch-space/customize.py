from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    if env.get('MLC_NVIDIA_MLPERF_SCRATCH_PATH', '') == '':
        if env.get('MLPERF_SCRATCH_PATH', '') != '':
            env['MLC_NVIDIA_MLPERF_SCRATCH_PATH'] = env['MLPERF_SCRATCH_PATH']
        else:
            env['MLC_NVIDIA_MLPERF_SCRATCH_PATH'] = os.getcwd()

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLPERF_SCRATCH_PATH'] = env['MLC_NVIDIA_MLPERF_SCRATCH_PATH']
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_NVIDIA_MLPERF_SCRATCH_PATH']

    return {'return': 0}
