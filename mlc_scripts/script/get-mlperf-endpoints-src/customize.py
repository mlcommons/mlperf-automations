from mlc import utils
from utils import is_true
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    env = i['env']
    meta = i['meta']

    script_path = i['run_script_input']['path']

    if env.get("MLC_MLPERF_LAST_RELEASE", '') == '':
        env["MLC_MLPERF_LAST_RELEASE"] = "v5.1"

    if 'MLC_GIT_DEPTH' not in env:
        env['MLC_GIT_DEPTH'] = ''

    if 'MLC_GIT_RECURSE_SUBMODULES' not in env:
        env['MLC_GIT_RECURSE_SUBMODULES'] = ''

    submodules = []

    # will add submodules in future if needed, for now none
    possible_submodules = {
    }

    for submodule in possible_submodules:
        env_name = submodule.upper().replace("-", "_")
        if is_true(env.get("MLC_SUBMODULE_" + env_name)):
            submodules.append(possible_submodules[submodule])

    env['MLC_GIT_SUBMODULES'] = ",".join(submodules)

    if env.get('MLC_GIT_PATCH_FILENAME', '') != '':
        patch_file_name = env['MLC_GIT_PATCH_FILENAME']
        env['MLC_GIT_PATCH_FILEPATHS'] = os.path.join(
            script_path, 'patch', patch_file_name)

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    endpoints_root = env['MLC_MLPERF_INFERENCE_ENDPOINTS_SOURCE']

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = endpoints_root

    env['+PYTHONPATH'] = []

    return {'return': 0}
