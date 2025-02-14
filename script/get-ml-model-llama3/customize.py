from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    # skip download and register in cache if the llama3 checkpoint path is
    # already defined by the user
    if env.get('MLC_ML_MODEL_LLAMA3_CHECKPOINT_PATH', '') != '':
        env['LLAMA3_CHECKPOINT_PATH'] = env['MLC_ML_MODEL_LLAMA3_CHECKPOINT_PATH']
        return {'return': 0}

    path = env.get('MLC_OUTDIRNAME', '').strip()

    if path != "":
        os.makedirs(path, exist_ok=True)
        env['MLC_GIT_CHECKOUT_FOLDER'] = os.path.join(
            path, env['MLC_ML_MODEL_NAME'])

    if env['MLC_DOWNLOAD_SRC'] == "mlcommons":
        i['run_script_input']['script_name'] = 'run-rclone'
        if env.get('MLC_OUTDIRNAME', '') != '':
            env['LLAMA3_CHECKPOINT_PATH'] = env['MLC_OUTDIRNAME']
        else:
            env['LLAMA3_CHECKPOINT_PATH'] = os.getcwd()
    env['MLC_TMP_REQUIRE_DOWNLOAD'] = 'yes'

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_ML_MODEL_LLAMA3_CHECKPOINT_PATH'] = env['LLAMA3_CHECKPOINT_PATH']
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ML_MODEL_PATH']

    return {'return': 0}
