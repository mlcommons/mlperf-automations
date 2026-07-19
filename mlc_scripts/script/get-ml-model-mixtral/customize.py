from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    path = env.get('MIXTRAL_CHECKPOINT_PATH', '').strip()

    if path == '' or not os.path.exists(path):
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'yes'

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if not env.get('MLC_DOWNLOAD_MODE', '') == "dry":
        if env.get('MIXTRAL_CHECKPOINT_PATH', '') == '':
            env['MIXTRAL_CHECKPOINT_PATH'] = env['MLC_ML_MODEL_PATH']
        else:
            env['MLC_ML_MODEL_PATH'] = env['MIXTRAL_CHECKPOINT_PATH']
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_PATH']

    return {'return': 0}
