from mlc import utils
import os


def postprocess(i):
    env = i['env']

    script_path = env['MLC_TMP_CURRENT_SCRIPT_PATH']

    env['MLC_DATASET_IMAGENET_HELPER_PATH'] = script_path
    env['+PYTHONPATH'] = [script_path]

    return {'return': 0}
