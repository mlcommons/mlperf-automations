from mlc import utils
from utils import is_true, is_false
import os
import shutil


def preprocess(i):

    env = i['env']

    if env.get('MLC_TMP_ML_MODEL', '') != "llama3_1-8b":
        if is_true(env.get('MLC_CNNDM_INTEL_VARIATION', '')):
            i['run_script_input']['script_name'] = "run-intel"
        else:
            print("Using MLCommons Inference source from '" +
                  env['MLC_MLPERF_INFERENCE_SOURCE'] + "'")
    else:
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    if env.get('MLC_OUTDIRNAME', '') != '':
        env['MLC_DOWNLOAD_PATH'] = env['MLC_OUTDIRNAME']

    return {'return': 0}


def postprocess(i):
    env = i['env']

    if env.get('MLC_TMP_ML_MODEL', '') != "llama3_1-8b":
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
    else:
        env['MLC_DATASET_CNNDM_EVAL_PATH'] = os.path.join(env['MLC_DATASET_CNNDM_EVAL_PATH'], env['MLC_DATASET_CNNDM_FILENAME'])

    return {'return': 0}
