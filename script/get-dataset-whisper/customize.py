from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}
    
    if env.get('MLC_DATASET_WHISPER_PATH', '') != '' :
        return {'return': 0 }

    print(env.get('MLC_TMP_DATASET_TYPE', ''))
    if env.get('MLC_TMP_DATASET_TYPE', '') == "preprocessed":
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"
    else:
        cwd = env.get('MLC_OUTDIRNAME', os.getcwd())
        data_dir = os.path.join(cwd, 'data')
        env['MLC_TMP_DATA_DIR'] = data_dir
        librispeech_dir = os.path.join(cwd, 'LibriSpeech')
        env['MLC_TMP_LIBRISPEECH_DIR'] = librispeech_dir
        utils_dir = os.path.join(env['MLC_MLPERF_INFERENCE_SOURCE'], 'speech2text', 'utils')
        env['MLC_TMP_UTILS_DIR'] = utils_dir
        env['MLC_DATASET_WHISPER_PATH'] = data_dir

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
