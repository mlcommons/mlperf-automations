from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if is_true(env.get('MLC_ML_MODEL_TF_FIX_INPUT_SHAPE', '')):
        i['run_script_input']['script_name'] = "run-fix-input"

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if is_true(env.get('MLC_ML_MODEL_TF_FIX_INPUT_SHAPE', '')):
        env['MLC_ML_MODEL_STARTING_FILE_PATH'] = env['MLC_ML_MODEL_FILE_WITH_PATH']
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = os.path.join(
            os.getcwd(), "resnet50_v1.pb")

    env['MLC_ML_MODEL_FILE'] = os.path.basename(
        env['MLC_ML_MODEL_FILE_WITH_PATH'])
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_FILE_WITH_PATH']

    env['MLC_DOWNLOAD_PATH'] = os.path.dirname(
        env['MLC_ML_MODEL_FILE_WITH_PATH'])

    return {'return': 0}
