from mlc import utils
from utils import is_true, is_false
import os
import shutil


def preprocess(i):

    env = i['env']

    if is_true(env.get('MLC_CNNDM_INTEL_VARIATION', '')):
        i['run_script_input']['script_name'] = "run-intel"
    else:
        print("Using MLCommons Inference source from '" +
              env['MLC_MLPERF_INFERENCE_SOURCE'] + "'")

    return {'return': 0}


def postprocess(i):
    env = i['env']

    if is_false(env.get('MLC_DATASET_CALIBRATION', '')):
        env['MLC_DATASET_PATH'] = os.path.join(os.getcwd(), 'install')
        env['MLC_DATASET_EVAL_PATH'] = os.path.join(
            os.getcwd(), 'install', 'cnn_eval.json')
        env['MLC_DATASET_CNNDM_EVAL_PATH'] = os.path.join(
            os.getcwd(), 'install', 'cnn_eval.json')
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_DATASET_PATH']
    else:
        env['MLC_CALIBRATION_DATASET_PATH'] = os.path.join(
            os.getcwd(), 'install', 'cnn_dailymail_calibration.json')
        env['MLC_CALIBRATION_DATASET_CNNDM_PATH'] = os.path.join(
            os.getcwd(), 'install', 'cnn_dailymail_calibration.json')
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_CALIBRATION_DATASET_PATH']

    return {'return': 0}
