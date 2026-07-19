from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    return {'return': 0}


def postprocess(i):
    env = i['env']

    env['MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH'] = os.path.join(
        env['MLC_MLPERF_INFERENCE_RESULTS_PATH'], "closed", "NVIDIA")
    env['+PYTHONPATH'] = [env['MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH']]

    return {'return': 0}
