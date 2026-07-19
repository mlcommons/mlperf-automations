from mlc import utils
import os
import shutil


def preprocess(i):

    env = i['env']

    print("Using MLCommons Inference source from '" +
          env['MLC_MLPERF_INFERENCE_SOURCE'] + "'")
    preprocess_src = os.path.join(
        env['MLC_MLPERF_INFERENCE_RNNT_PATH'],
        'pytorch',
        'utils',
        'convert_librispeech.py')
    cmd = 'cd ' + env['MLC_MLPERF_INFERENCE_3DUNET_PATH'] + ' && ${MLC_PYTHON_BIN_WITH_PATH} ' + preprocess_src + ' --input_dir ' + env['MLC_DATASET_LIBRISPEECH_PATH'] + \
        ' --dest_dir ' + os.path.join(os.getcwd(), 'dev-clean-wav') + \
        ' --output_json ' + os.path.join(os.getcwd(), 'dev-clean-wav.json')
    env['MLC_TMP_CMD'] = cmd

    return {'return': 0}


def postprocess(i):
    env = i['env']
    env['MLC_DATASET_PREPROCESSED_PATH'] = os.path.join(
        os.getcwd(), 'dev-clean-wav')
    env['MLC_DATASET_PREPROCESSED_JSON'] = os.path.join(
        os.getcwd(), 'dev-clean-wav.json')

    return {'return': 0}
