from mlc import utils
import os
from utils import is_true


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if is_true(env.get('MLC_DATASET_MIXTRAL_GENERATE_TEST_DATA', '')):
        env['MLC_DATASET_MIXTRAL_TEST_DATA_GENERATED_PATH'] = os.path.join(
            os.getcwd(), "mixtral-test-dataset.pkl")

    return {'return': 0}


def postprocess(i):
    env = i['env']

    if not env.get('MLC_DOWNLOAD_MODE', '') == "dry":
        env['MLC_DATASET_MIXTRAL_PREPROCESSED_PATH'] = env['MLC_DATASET_PREPROCESSED_PATH']

        if env.get('MLC_DOWNLOAD_TOOL', '') == "r2-downloader":
            if env.get('MLC_DATASET_TYPE', '') == 'validation':
                env['MLC_DATASET_MIXTRAL_PREPROCESSED_PATH'] = os.path.join(
                    env['MLC_DATASET_PREPROCESSED_PATH'], '09292024_mixtral_15k_mintoken2_v1.pkl')
            elif env.get('MLC_DATASET_TYPE', '') == 'calibration':
                env['MLC_DATASET_MIXTRAL_PREPROCESSED_PATH'] = os.path.join(
                    env['MLC_DATASET_PREPROCESSED_PATH'], '2024.06.06_mixtral_15k_calibration_v4.pkl')

        if is_true(env.get('MLC_DATASET_MIXTRAL_GENERATE_TEST_DATA', '')):
            env['MLC_DATASET_MIXTRAL_PREPROCESSED_PATH'] = env['MLC_DATASET_MIXTRAL_TEST_DATA_GENERATED_PATH']

    return {'return': 0}
