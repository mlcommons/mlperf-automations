from mlc import utils
import os
import shutil


def preprocess(i):

    env = i['env']

    print("Using MLCommons Inference source from '" +
          env['MLC_MLPERF_INFERENCE_SOURCE'] + "'")
    preprocess_src = os.path.join(
        env['MLC_MLPERF_INFERENCE_3DUNET_PATH'],
        'preprocess.py')
    cmd = 'cd ' + env['MLC_MLPERF_INFERENCE_3DUNET_PATH'] + \
        ' && ${MLC_PYTHON_BIN_WITH_PATH} preprocess.py --raw_data_dir ' + \
        env['MLC_DATASET_PATH'] + ' --results_dir ' + \
        os.getcwd() + ' --mode preprocess'
    env['MLC_TMP_CMD'] = cmd

    return {'return': 0}


def postprocess(i):
    env = i['env']
    if 'MLC_DATASET_PREPROCESSED_PATH' not in env:
        env['MLC_DATASET_PREPROCESSED_PATH'] = os.getcwd()
        env['MLC_DATASET_KITS19_PREPROCESSED_PATH'] = env['MLC_DATASET_PREPROCESSED_PATH']

    return {'return': 0}
