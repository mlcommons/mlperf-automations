from mlc import utils
from utils import *
import os
import shutil
import importlib.util
import json


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
        target_dir = os.path.join(
            env['MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH'],
            "configs",
            system_name,
            scenario)
        os.makedirs(target_dir, exist_ok=True)
        src_file = os.path.join(tmp_script_path, "dummy_config.py")

        dest_file = os.path.join(target_dir, f"{mlc_model}.py")

        dummy_config_path = os.path.join(tmp_script_path, "dummy_config.py")
        spec = importlib.util.spec_from_file_location(
            "dummy_config", dummy_config_path)
        dummy_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dummy_module)

        EXPORTS = dummy_module.EXPORTS

        # --- Example dynamic insertion ---
        if mlc_model == "llama2-70b":
            for k, v in EXPORTS.items():
                if isinstance(v, dict):
                    v.setdefault('llm_fields.llm_gen_config_path',
                                 'code/llama2-70b/tensorrt/generation_config.json')

        # --- Write modified config to destination ---
        with open(dest_file, "w") as f:
            f.write("# Auto-generated config\n\n")
            f.write("EXPORTS = ")
            f.write(repr(EXPORTS))
            f.write("\n")

    return {'return': 0}
