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
        if env.get('MLC_DOWNLOAD_TOOL', '') == "rclone":
            env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'] = os.path.join(
                env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'],
                env['MLC_DATASET_NUSCENES_EXTRACTED_FOLDER_NAME'])
        elif env.get('MLC_DOWNLOAD_TOOL', '') == "r2-downloader":
            env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'] = os.path.join(
                env['MLC_PREPROCESSED_DATASET_NUSCENES_PATH'],
                "preprocessed",
                env['MLC_DATASET_NUSCENES_EXTRACTED_FOLDER_NAME'])

        if env.get('MLC_DOWNLOAD_TOOL', '') == "rclone":
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

    # Ensure scene_lengths.pkl is alongside the dataset directory regardless of how it was obtained
    dataset_path = env.get('MLC_PREPROCESSED_DATASET_NUSCENES_PATH', '').rstrip('/')
    pickle_filename = env.get('MLC_DATASET_NUSCENES_SCENE_PICKLE_FILENAME', 'scene_lengths.pkl')
    if dataset_path:
        expected = os.path.join(os.path.dirname(dataset_path), pickle_filename)
        if not os.path.exists(expected):
            # Look one level higher (e.g. when downloaded outside the preprocessed dir)
            candidate = os.path.join(os.path.dirname(os.path.dirname(dataset_path)), pickle_filename)
            if os.path.exists(candidate):
                shutil.copy(candidate, expected)

    return {'return': 0}
