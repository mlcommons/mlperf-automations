from mlc import utils
import os
from utils import is_true


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_ML_MODEL_DEEPLABV3_PLUS_PATH', '') == '':
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if is_true(env.get('MLC_TMP_REQUIRE_DOWNLOAD', '')):
        env['MLC_ML_MODEL_DEEPLABV3_PLUS_PATH'] = os.path.join(
            env['MLC_ML_MODEL_DEEPLABV3_PLUS_PATH'], env['MLC_ML_MODEL_FILENAME'])
    env['MLC_ML_MODEL_FILE_WITH_PATH'] = env['MLC_ML_MODEL_DEEPLABV3_PLUS_PATH']

    return {'return': 0}
