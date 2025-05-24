from mlc import utils
import os
import shutil
from utils import is_true


def preprocess(i):

    env = i['env']

    if env.get('MLC_NUSCENES_DATASET_TYPE', '') == "prebuilt" and env.get(
            'MLC_PREPROCESSED_DATASET_NUSCENES_PATH', '') == '':
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    return {'return': 0}


def postprocess(i):
    env = i['env']

    if is_true(env.get('MLC_TMP_REQUIRE_DOWNLOAD', '')):
        env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'] = os.path.join(
            env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'],
            env['MLC_DATASET_NUSCENES_EXTRACTED_FOLDER_NAME'])
        env['MLC_PREPROCESSED_DATASET_NUSCENES_ACC_CHECKER_MIN_FILES_PATH'] = os.path.join(
            env['MLC_PREPROCESSED_DATASET_NUSCENES_ACC_CHECKER_MIN_FILES_PATH'],
            env['MLC_DATASET_NUSCENES_ACC_REQ_FILE_EXTRACTED_FOLDER_NAME'])
        if env.get(
                'MLC_PREPROCESSED_DATASET_NUSCENES_SCENE_LENGTHS_PATH', '') != '':
            shutil.copy(
                os.path.join(
                    env['MLC_PREPROCESSED_DATASET_NUSCENES_SCENE_LENGTHS_PATH'],
                    env['MLC_DATASET_NUSCENES_SCENE_PICKLE_FILENAME']),
                os.path.join(
                    os.path.dirname(
                        env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'].rstrip("/")),
                    env['MLC_DATASET_NUSCENES_SCENE_PICKLE_FILENAME']))

    return {'return': 0}
