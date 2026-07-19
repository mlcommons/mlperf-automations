from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    automation = i['automation']

    cm = automation.action_object

    script_path = i['run_script_input']['path']

    path = env.get('MLC_DOWNLOAD_PATH', '')
    if path == '':
        path = os.getcwd()

    if not is_true(env.get('MLC_GIT_CLONE_REPO', '')):
        run_cmd = env.get('MLC_PYTHON_BIN_WITH_PATH') + " " + \
            os.path.join(script_path, 'download_model.py')
    else:
        run_cmd = ''

    env['MLC_RUN_CMD'] = run_cmd

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env_key = env.get('MLC_MODEL_ZOO_ENV_KEY', '')

    path_file = env.get('MLC_ML_MODEL_FILE_WITH_PATH', '')
    if path_file != '':
        path_dir = os.path.dirname(path_file)

        env['MLC_ML_MODEL_PATH'] = path_dir

        if env_key != '':
            env['MLC_ML_MODEL_' + env_key + '_PATH'] = path_dir

    else:
        path_dir = env['MLC_ML_MODEL_PATH']

    if env_key != '':
        env['MLC_ML_MODEL_' + env_key + '_FILE_WITH_PATH'] = path_dir

    return {'return': 0}
