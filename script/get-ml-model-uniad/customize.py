from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    logger = i['automation'].logger

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_ML_MODEL_UNIAD_PATH', '') == '':
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"
    else:
        if os.path.exists(env['MLC_ML_MODEL_UNIAD_PATH']):
            return {'return': 0}
        else:
            logger.warning(f'Provided UNIAD path {env['MLC_ML_MODEL_UNIAD_PATH']} does not exist. Proceeding for download...')
            env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE', '') != 'dry':
        if env.get('MLC_TMP_REQUIRE_DOWNLOAD', '') == "yes":
            env['MLC_ML_MODEL_UNIAD_PATH'] = os.path.join(
                env['MLC_ML_MODEL_UNIAD_PATH'], 'tiny_imgx0.25_e2e_ep20.pth')
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = env['MLC_ML_MODEL_UNIAD_PATH']

    return {'return': 0}
