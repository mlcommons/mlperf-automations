from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    if env.get(
            'MLC_ML_DATASET_MLPERF_INFERENCE_DLRMV3_SYNTHETIC_STREAMING_PATH', '') == '':
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE', '') != 'dry':
        env['MLC_ML_DATASET_FILE_WITH_PATH'] = env['MLC_ML_DATASET_MLPERF_INFERENCE_DLRMV3_SYNTHETIC_STREAMING_PATH']

    return {'return': 0}
