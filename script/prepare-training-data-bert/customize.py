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

    env['MLC_BERT_CONFIG_DOWNLOAD_DIR'] = os.path.join(datadir, "phase1")
    env['MLC_BERT_VOCAB_DOWNLOAD_DIR'] = os.path.join(datadir, "phase1")
    env['MLC_BERT_DATA_DOWNLOAD_DIR'] = os.path.join(datadir, "download")

    env['MLC_BERT_CHECKPOINT_DOWNLOAD_DIR'] = os.path.join(datadir, "phase1")

    if env.get("MLC_TMP_VARIATION", "") == "nvidia":
        code_path = os.path.join(
            env['MLC_GIT_REPO_CHECKOUT_PATH'],
            'NVIDIA',
            'benchmarks',
            'bert',
            'implementations',
            'pytorch-22.09')
        env['MLC_RUN_DIR'] = code_path
    elif env.get("MLC_TMP_VARIATION", "") == "reference":
        code_path = os.path.join(
            env['MLC_MLPERF_TRAINING_SOURCE'],
            'language_model',
            'tensorflow',
            'bert',
            'cleanup_scripts')
        env['MLC_RUN_DIR'] = code_path

    return {'return': 0}


def postprocess(i):

    env = i['env']

    data_dir = env['MLC_DATA_DIR']
    env['MLC_MLPERF_TRAINING_BERT_DATA_PATH'] = data_dir

    if env.get("MLC_TMP_VARIATION", "") == "nvidia":
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = os.path.join(
            data_dir, "hdf5", "eval", "eval_all.hdf5")
    elif env.get("MLC_TMP_VARIATION", "") == "reference":
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = os.path.join(
            data_dir, "tfrecords", "eval_10k")
        env['MLC_MLPERF_TRAINING_BERT_TFRECORDS_PATH'] = os.path.join(
            data_dir, "tfrecords")

    env['MLC_MLPERF_TRAINING_BERT_VOCAB_PATH'] = env['MLC_BERT_VOCAB_FILE_PATH']
    env['MLC_MLPERF_TRAINING_BERT_CONFIG_PATH'] = env['MLC_BERT_CONFIG_FILE_PATH']

    return {'return': 0}
