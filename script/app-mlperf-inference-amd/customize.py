from mlc import utils
from utils import is_true
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}
    env = i['env']

    if is_true(env.get('MLC_MLPERF_SKIP_RUN', '')):
        return {'return': 0}

    env['MLC_MLPERF_AMD_SCRIPT_PATH'] = env['MLC_TMP_CURRENT_SCRIPT_PATH']
    env['MLC_MLPERF_AMD_CODE_PATH'] = os.path.join(
        env['MLC_MLPERF_INFERENCE_IMPLEMENTATION_REPO'], "closed", "AMD")

    if 'MLC_MODEL' not in env:
        return {
            'return': 1, 'error': 'Please select a variation specifying the model to run'}
    if 'MLC_MLPERF_BACKEND' not in env:
        return {'return': 1,
                'error': 'Please select a variation specifying the backend'}
    if 'MLC_MLPERF_DEVICE' not in env:
        return {
            'return': 1, 'error': 'Please select a variation specifying the device to run on'}

    if "llama2" in env['MLC_MODEL']:
        env['MLC_RUN_DIR'] = i['run_script_input']['path']
        env['MLC_MLPERF_AMD_LLAMA2_CODE_PATH'] = os.path.join(
            env['MLC_MLPERF_AMD_CODE_PATH'], "llama2-70b-99.9/VllmFp8")
        env['MLC_RUN_CMD'] = "bash run-llama2.sh "
    else:
        return {'return': 1, 'error': 'Model {} not supported'.format(
            env['MLC_MODEL'])}

    return {'return': 0}
    # return {'return':1, 'error': 'Run command needs to be tested'}


def postprocess(i):

    env = i['env']

    return {'return': 0}
