from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    # If MLC_ML_MODEL_LLAMA3_CHECKPOINT_PATH already points to a valid directory
    # (e.g. remapped /mlc-mount/... path inside Docker), use it and sync
    # LLAMA3_CHECKPOINT_PATH so postprocess doesn't override it back.
    mlc_path = env.get('MLC_ML_MODEL_LLAMA3_CHECKPOINT_PATH', '').strip()
    if mlc_path and os.path.isdir(mlc_path):
        env['LLAMA3_CHECKPOINT_PATH'] = mlc_path
        return {'return': 0}

    # skip download and register in cache if the llama3 checkpoint path is
    # already defined by the user
    if env.get('LLAMA3_CHECKPOINT_PATH', '') != '':
        env['MLC_ML_MODEL_LLAMA3_CHECKPOINT_PATH'] = env['LLAMA3_CHECKPOINT_PATH']
        return {'return': 0}

    path = env.get('MLC_OUTDIRNAME', '').strip()

    if path != "" and env.get('MLC_DOWNLOAD_SRC', '') == "huggingface":
        os.makedirs(path, exist_ok=True)
        env['MLC_GIT_CHECKOUT_FOLDER'] = os.path.join(
            path, env['MLC_ML_MODEL_NAME'])

    env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'yes'

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE', '') != "dry":
        if env.get('MLC_ML_MODEL_PATH', '') != '':
            env['LLAMA3_CHECKPOINT_PATH'] = env['MLC_ML_MODEL_PATH']
        else:
            env['MLC_ML_MODEL_PATH'] = env['LLAMA3_CHECKPOINT_PATH']
        env['MLC_ML_MODEL_LLAMA3_CHECKPOINT_PATH'] = env['LLAMA3_CHECKPOINT_PATH']
        env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_LLAMA3_CHECKPOINT_PATH']

    return {'return': 0}
