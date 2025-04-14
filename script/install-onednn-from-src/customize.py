from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    run_cmd = ""

    env['MLC_RUN_CMD'] = run_cmd
    env['MLC_ONEDNN_INSTALLED_PATH'] = os.path.join(os.getcwd(), "onednn")

    if is_true(env.get('MLC_FOR_INTEL_MLPERF_INFERENCE_BERT', '')):
        i['run_script_input']['script_name'] = "run-intel-mlperf-inference-bert"

    automation = i['automation']

    recursion_spaces = i['recursion_spaces']

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
