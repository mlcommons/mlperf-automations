from mlc import utils
import os


def preprocess(i):
    env = i['env']

    path = env.get('MLC_DATASET_FRAMES_PATH', '').strip()

    if path == '' or not os.path.exists(path):
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'yes'

    return {'return': 0}


def postprocess(i):
    env = i['env']

    if not env.get('MLC_DOWNLOAD_MODE', '') == 'dry':
        dataset_path = env.get('MLC_DATASET_FRAMES_PATH', '')
        if dataset_path == '':
            dataset_path = env.get('MLC_DATASET_PATH', '')
            env['MLC_DATASET_FRAMES_PATH'] = dataset_path
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = dataset_path

    return {'return': 0}
