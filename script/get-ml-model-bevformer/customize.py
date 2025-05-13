from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_ML_MODEL_BEVFORMER_PATH'] = os.path.join(
        env['MLC_ML_MODEL_BEVFORMER_PATH'], env['MLC_ML_MODEL_FILENAME'])

    return {'return': 0}
