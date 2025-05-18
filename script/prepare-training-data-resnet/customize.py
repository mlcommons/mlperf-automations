from mlc import utils
import os
from utils import is_true


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    datadir = env.get('MLC_DATA_DIR', os.getcwd())
    env['MLC_DATA_DIR'] = datadir

    env['MXNET_VER'] = env.get('MLC_MXNET_VER', '22.08').replace("-", ".")

    env['MLC_IMAGENET_LABELS_DOWNLOAD_DIR'] = env['MLC_DATASET_IMAGENET_TRAIN_PATH']

    if env.get("MLC_TMP_VARIATION", "") == "nvidia":
        code_path = os.path.join(
            env['MLC_NVIDIA_DEEPLEARNING_EXAMPLES_REPO_PATH'],
            'MxNet',
            'Classification',
            'RN50v1.5')
        env['MLC_RUN_DIR'] = code_path
        i['run_script_input']['script_name'] = "run-nvidia"

    elif env.get("MLC_TMP_VARIATION", "") == "reference":
        code_path = os.path.join(
            env['MLC_MLPERF_TRAINING_SOURCE'],
            'image_classification',
            'tensorflow2')
        env['MLC_RUN_DIR'] = code_path
        i['run_script_input']['script_name'] = "run-reference"

    return {'return': 0}


def postprocess(i):

    env = i['env']

    data_dir = env['MLC_DATA_DIR']
    env['MLC_MLPERF_TRAINING_RESNET_DATA_PATH'] = data_dir

    env['MLC_MLPERF_TRAINING_IMAGENET_PATH'] = env['MLC_DATASET_IMAGENET_TRAIN_PATH']

    if env.get("MLC_TMP_VARIATION", "") == "nvidia":
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = data_dir
        env['MLC_MLPERF_TRAINING_NVIDIA_RESNET_PREPROCESSED_PATH'] = data_dir

    elif env.get("MLC_TMP_VARIATION", "") == "reference":
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = os.path.join(
            data_dir, "tfrecords")
        env['MLC_MLPERF_TRAINING_RESNET_TFRECORDS_PATH'] = os.path.join(
            data_dir, "tfrecords")

    return {'return': 0}
