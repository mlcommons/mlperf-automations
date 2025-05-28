from mlc import utils
import os
import shutil
from utils import is_true


def preprocess(i):

    env = i['env']

    if env.get('MLC_NUSCENES_DATASET_TYPE', '') == "prebuilt" and env.get(
            'MLC_PREPROCESSED_DATASET_COGNATA_PATH', '') == '':
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    return {'return': 0}


def postprocess(i):
    env = i['env']
    if is_true(env.get('MLC_TMP_REQUIRE_DOWNLOAD', '')):
        env['MLC_PREPROCESSED_DATASET_COGNATA_PATH'] = os.path.join(
            env['MLC_PREPROCESSED_DATASET_COGNATA_PATH'],
            env['MLC_DATASET_COGNATA_EXTRACTED_FOLDER_NAME'])

    return {'return': 0}
