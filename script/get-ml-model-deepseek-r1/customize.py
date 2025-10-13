from mlc import utils
import os
from utils import is_true


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_ML_MODEL_DEEPSEEK_R1_PATH', '') == '':
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"
    elif not os.path.exists(env['MLC_ML_MODEL_DEEPSEEK_R1_PATH']):
        return {'return': 1, 'error': f"Path {env['MLC_ML_MODEL_DEEPSEEK_R1_PATH']} does not exists!"}

    return {'return': 0}


def postprocess(i):

    env = i['env']
    
    if not env.get('MLC_DOWNLOAD_MODE', '') == "dry":
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = env['MLC_ML_MODEL_DEEPSEEK_R1_PATH']

    return {'return': 0}
