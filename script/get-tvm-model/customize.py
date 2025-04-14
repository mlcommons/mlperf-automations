from mlc import utils
import os
from utils import is_true

def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    work_dir = env.get('MLC_TUNE_TVM_MODEL_WORKDIR', '')

    if work_dir != '':
        if not os.path.exists(work_dir):
            raise FileNotFoundError(
                f"Error: the specified path \"{work_dir}\"does not exist")

        if not os.path.exists(f"{work_dir}/database_workload.json"):
            raise FileNotFoundError(
                "Error: the found workdir does not contain database_workload.json")

        if not os.path.exists(f"{work_dir}/database_tuning_record.json"):
            raise FileNotFoundError(
                "Error: the found workdir does not contain database_tuning_record.json")

        if env.get('MLC_TUNE_TVM_MODEL', '') != '':
            print("The \"tune-model\" variation is selected, but at the same time the path to the existing \"work_dir\" is also specified. The compiled model will be based on the found existing \"work_dir\".")
            env["MLC_TUNE_TVM_MODEL"] = "no"

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_ML_MODEL_ORIGINAL_FILE_WITH_PATH'] = env['MLC_ML_MODEL_FILE_WITH_PATH']
    env['MLC_ML_MODEL_FILE'] = 'model-tvm.so'
    env['MLC_ML_MODEL_PATH'] = os.path.join(os.getcwd())
    env['MLC_ML_MODEL_FILE_WITH_PATH'] = os.path.join(
        os.getcwd(), env['MLC_ML_MODEL_FILE'])
    env['MLC_ML_MODEL_FRAMEWORK'] = "tvm-" + env['MLC_ML_MODEL_FRAMEWORK']
    if 'MLC_ML_MODEL_INPUT_SHAPES' in env.keys():
        env['MLC_ML_MODEL_INPUT_SHAPES'] = env['MLC_ML_MODEL_INPUT_SHAPES'].replace(
            "BATCH_SIZE", env['MLC_ML_MODEL_MAX_BATCH_SIZE'])
    if 'MLC_TVM_FRONTEND_FRAMEWORK' in env and env['MLC_TVM_FRONTEND_FRAMEWORK'] == 'pytorch':
        env['MLC_PREPROCESS_PYTORCH'] = 'yes'
    return {'return': 0}
