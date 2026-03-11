from mlc import utils
import os
import shutil
from utils import is_true


def preprocess(i):

    env = i['env']

    logger = i['automation'].logger

    if env.get('MLC_NUSCENES_DATASET_TYPE', '') == "prebuilt":
        if env.get('MLC_PREPROCESSED_DATASET_NUSCENES_PATH', '') == '':
            env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"
        else:
            if os.path.exists(env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH']):
                return {'return': 0}
            else:
                logger.warning(f"Provided Nuscenes path {env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH']} does not exist. Proceeding for download...")
                env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"

    return {'return': 0}


def postprocess(i):
    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE', '') != "dry":
        if env.get('MLC_DOWNLOAD_TOOL', '') == "rclone" and is_true(
                env.get('MLC_TMP_REQUIRE_DOWNLOAD', '')):
            env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'] = os.path.join(
                env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'],
                env['MLC_DATASET_NUSCENES_EXTRACTED_FOLDER_NAME'])
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

        elif env.get('MLC_DOWNLOAD_TOOL', '') == "r2-downloader" or not is_true(env.get('MLC_TMP_REQUIRE_DOWNLOAD', '')):
            env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'] = os.path.join(
                env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'],
                "preprocessed",
                env['MLC_DATASET_NUSCENES_EXTRACTED_FOLDER_NAME'])
            env['MLC_PREPROCESSED_DATASET_NUSCENES_SCENE_LENGTHS_PATH'] = os.path.join(
                env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'], "scene_lengths.pkl")
            env['MLC_PREPROCESSED_DATASET_NUSCENES_ACC_CHECKER_MIN_FILES_PATH'] = env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH']

    return {'return': 0}
