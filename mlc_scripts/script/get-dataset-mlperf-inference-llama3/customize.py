from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get('MLC_DATASET_LLAMA3_PATH', '') == '':
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    if env.get('MLC_OUTDIRNAME', '') != '':
        env['MLC_DOWNLOAD_PATH'] = env['MLC_OUTDIRNAME']

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if is_true(env.get('MLC_TMP_REQUIRE_DOWNLOAD', '')):
        env['MLC_DATASET_LLAMA3_PATH'] = os.path.join(
            env['MLC_DATASET_LLAMA3_PATH'], env['MLC_DATASET_FILE_NAME'])

    return {'return': 0}
