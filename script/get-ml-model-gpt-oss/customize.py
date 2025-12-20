from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}
    
    path = env.get('MLC_ML_MODEL_GPT_OSS_PATH', '').strip()
    if path == '' or not os.path.exists(path):
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'yes'

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE', '') != 'dry': 
        if env.get('MLC_DOWNLOAD_SRC', '') == 'mlc':
            env['MLC_ML_MODEL_FILE_WITH_PATH'] = env['MLC_ML_MODEL_GPT_OSS_PATH']
        elif env.get('MLC_DOWNLOAD_SRC', '') == 'huggingface':
            env['MLC_ML_MODEL_FILE_WITH_PATH'] = env['MLC_ML_MODEL_PATH']
            env['MLC_ML_MODEL_GPT_OSS_PATH'] = env['MLC_ML_MODEL_PATH']

    return {'return': 0}
