from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if os_info['platform'] == "windows":
        return {'return': 1, 'error': 'Script not supported in windows yet!'}

    checkpoint_path = env.get('MLC_ML_MODEL_WHISPER_PATH', '').strip()

    if checkpoint_path == '':
        env['MLC_TMP_REQUIRE_DOWNLOAD'] = "yes"
    else:
        # Normalize and expand the path
        checkpoint_path = os.path.abspath(os.path.expanduser(checkpoint_path))
        env['MLC_ML_MODEL_WHISPER_PATH'] = checkpoint_path

        if not os.path.exists(checkpoint_path):
            return {
                'return': 1,
                'error': f"Provided Whisper model path '{checkpoint_path}' does not exist."
            }

        if not os.path.isdir(checkpoint_path):
            return {
                'return': 1,
                'error': f"Provided Whisper model path '{checkpoint_path}' is not a directory."
            }

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE', '') != "dry":
        env['MLC_ML_MODEL_FILE_WITH_PATH'] = env['MLC_ML_MODEL_WHISPER_PATH']

    return {'return': 0}
