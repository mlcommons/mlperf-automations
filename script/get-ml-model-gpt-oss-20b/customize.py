from mlc import utils
import os


def preprocess(i):
    env = i['env']

    path = env.get('MLC_ML_MODEL_GPT_OSS_20B_PATH', '').strip()

    if path == '' or not os.path.exists(path):
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'yes'

    return {'return': 0}


def postprocess(i):
    env = i['env']

    if not env.get('MLC_DOWNLOAD_MODE', '') == 'dry':
        model_path = env.get('MLC_ML_MODEL_GPT_OSS_20B_PATH', '')
        if model_path == '':
            model_path = env.get('MLC_ML_MODEL_PATH', '')
            env['MLC_ML_MODEL_GPT_OSS_20B_PATH'] = model_path
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = model_path

    return {'return': 0}
