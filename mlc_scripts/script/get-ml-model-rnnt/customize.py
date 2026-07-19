from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    automation = i['automation']

    logger = automation.logger

    cm = automation.action_object

    path = os.getcwd()

    url = env['MLC_PACKAGE_URL']

    logger.info('Downloading from {}'.format(url))

    r = cm.access({'action': 'download_file',
                   'automation': 'utils,dc2743f8450541e3',
                   'url': url})
    if r['return'] > 0:
        return r

    filename = r['filename']

    if is_true(env.get('MLC_UNZIP')):
        os.system("unzip " + filename)
        filename = env['MLC_ML_MODEL_FILE']
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = os.path.join(path, filename)
    else:
        # Add to path
        env['MLC_ML_MODEL_FILE'] = filename
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = r['path']

    env['MLC_ML_MODEL_PATH'] = path

    return {'return': 0}
