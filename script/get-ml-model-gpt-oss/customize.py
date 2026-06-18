from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    size = env.get('MLC_ML_MODEL_SIZE', '120b')
    path_env_key = f'MLC_ML_MODEL_GPT_OSS_{size.upper()}_PATH'

    path = env.get(path_env_key, env.get('MLC_ML_MODEL_GPT_OSS_PATH', '')).strip()
    if path == '' or not os.path.exists(path):
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'yes'

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE', '') != 'dry':
        size = env.get('MLC_ML_MODEL_SIZE', '120b')
        path_env_key = f'MLC_ML_MODEL_GPT_OSS_{size.upper()}_PATH'

        if env.get('MLC_DOWNLOAD_SRC', '') == 'huggingface':
            model_path = env.get('MLC_ML_MODEL_PATH', '')
            env['MLC_ML_MODEL_GPT_OSS_PATH'] = model_path
        else:
            model_path = env.get('MLC_ML_MODEL_GPT_OSS_PATH', '')
            if model_path == '':
                model_path = env.get('MLC_ML_MODEL_PATH', '')
                env['MLC_ML_MODEL_GPT_OSS_PATH'] = model_path

        env[path_env_key] = model_path
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = model_path
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = model_path

    return {'return': 0}
