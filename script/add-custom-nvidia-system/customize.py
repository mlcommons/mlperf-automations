from mlc import utils
from utils import *
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH']

    if is_true(env.get('MLC_CUSTOM_CONFIG', '')):
        state = i['state']
        system_meta = state['MLC_SUT_META']
        with open(os.path.join(env['MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH'], "systems", f"{env.get('MLC_NVIDIA_SYSTEM_NAME')}.json"), "w") as fp:
            json.dump(system_meta, fp, indent=2)
        # copy the dummy config file to proper location
        system_name = env["MLC_NVIDIA_SYSTEM_NAME"]
        scenario = env["MLC_MLPERF_LOADGEN_SCENARIO"]
        tmp_script_path = env["MLC_TMP_CURRENT_SCRIPT_PATH"]
        mlc_model = env["MLC_MODEL"]
        if "llama2-70b" in mlc_model:
            mlc_model = "llama2-70b"
        target_dir = os.path.join(env['MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH'], "configs", system_name, scenario)
        os.makedirs(target_dir, exist_ok=True)
        src_file = os.path.join(tmp_script_path, "dummy_config.py")

        dest_file = os.path.join(target_dir, f"{mlc_model}.py")
        shutil.copy(src_file, dest_file)

    return {'return': 0}
