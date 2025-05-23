import os
from utils import *


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    automation = i['automation']

    logger = automation.logger

    cm = automation.action_object

    path = os.getcwd()

    url = env['MLC_PACKAGE_URL']
    env['MLC_ML_MODEL_STARTING_WEIGHTS_FILENAME'] = url

    logger.info('Downloading from {}'.format(url))

    r = download_file({'url': url})
    if r['return'] > 0:
        return r

    filename = r['filename']

    if is_true(env.get('MLC_UNZIP')) or is_true(env.get('MLC_UNTAR')):
        if is_true(env.get('MLC_UNZIP')):
            cmd = "unzip "
        elif is_true(env.get('MLC_UNTAR')):
            cmd = "tar -xvzf "
        os.system(cmd + filename)

        filename = env['MLC_ML_MODEL_FILE']

        extract_folder = env.get('MLC_EXTRACT_FOLDER', '')

        if extract_folder:
            env['MLC_ML_MODEL_FILE_WITH_PATH'] = os.path.join(
                path, extract_folder, filename)
        else:
            env['MLC_ML_MODEL_FILE_WITH_PATH'] = os.path.join(path, filename)
    else:
        env['MLC_ML_MODEL_FILE'] = filename
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = r['path']

    env['MLC_ML_MODEL_PATH'] = path

    if not os.path.exists(env['MLC_ML_MODEL_FILE_WITH_PATH']):
        return {
            'return': 1, 'error': f"Model file path {env['MLC_ML_MODEL_FILE_WITH_PATH']} not existing. Probably the model name {env['MLC_ML_MODEL_FILE']} in model meta is wrong"}

    return {'return': 0}
