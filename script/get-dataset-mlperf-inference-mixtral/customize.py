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

    env['MLC_DATASET_MIXTRAL_PREPROCESSED_PATH'] = env['MLC_DATASET_PREPROCESSED_PATH']

    if is_true(env.get('MLC_DATASET_MIXTRAL_GENERATE_TEST_DATA', '')):
        env['MLC_DATASET_MIXTRAL_PREPROCESSED_PATH'] = env['MLC_DATASET_MIXTRAL_TEST_DATA_GENERATED_PATH']

    return {'return': 0}
