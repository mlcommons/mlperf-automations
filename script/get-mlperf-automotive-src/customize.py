from mlc import utils
from utils import is_true
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    env = i['env']
    meta = i['meta']

    script_path = i['run_script_input']['path']

    if env.get('MLC_GIT_CHECKOUT', '') == '' and env.get(
            'MLC_GIT_URL', '') == '' and env.get('MLC_VERSION', '') == '':
        # if custom checkout and url parameters are not set and MLC_VERSION is
        # not specified
        env['MLC_VERSION'] = "master"
        env["MLC_GIT_CHECKOUT"] = "master"
        env["MLC_GIT_URL"] = "https://github.com/mlcommons/mlperf_automotive"
    elif env.get('MLC_GIT_CHECKOUT', '') != '' and env.get('MLC_TMP_GIT_CHECKOUT', '') != '' and env.get('MLC_GIT_CHECKOUT', '') != env.get('MLC_TMP_GIT_CHECKOUT', ''):
        # if checkout branch is assigned inside version and custom branch is
        # also specified
        return {
            "return": 1, "error": "Conflicting branches between version assigned and user specified."}
    elif env.get('MLC_GIT_URL', '') != '' and env.get('MLC_TMP_GIT_URL', '') != '' and env.get('MLC_GIT_URL', '') != env.get('MLC_TMP_GIT_URL', ''):
        # if GIT URL is assigned inside version and custom branch is also
        # specified
        return {
            "return": 1, "error": "Conflicting URL's between version assigned and user specified."}

    if env.get('MLC_VERSION', '') == '':
        env['MLC_VERSION'] = "custom"

    # check whether branch and url is specified,
    # if not try to assign the values specified in version parameters,
    # if version parameters does not have the value to a parameter, set the
    # default one
    if env.get('MLC_GIT_CHECKOUT', '') == '' and env.get(
            'MLC_GIT_CHECKOUT_TAG', '') == '':
        if env.get('MLC_TMP_GIT_CHECKOUT', '') != '':
            env["MLC_GIT_CHECKOUT"] = env["MLC_TMP_GIT_CHECKOUT"]
        else:
            env["MLC_GIT_CHECKOUT"] = "master"

    if env.get('MLC_GIT_URL', '') == '':
        if env.get('MLC_TMP_GIT_URL', '') != '':
            env["MLC_GIT_URL"] = env["MLC_TMP_GIT_URL"]
        else:
            env["MLC_GIT_URL"] = "https://github.com/mlcommons/mlperf_automotive"

    if env.get("MLC_MLPERF_LAST_RELEASE", '') == '':
        env["MLC_MLPERF_LAST_RELEASE"] = "v0.5"

    if 'MLC_GIT_DEPTH' not in env:
        env['MLC_GIT_DEPTH'] = ''

    if 'MLC_GIT_RECURSE_SUBMODULES' not in env:
        env['MLC_GIT_RECURSE_SUBMODULES'] = ''
    submodules = []
    possible_submodules = {
        "pybind": "third_party/pybind",
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

    need_version = env.get('MLC_VERSION', '')
    versions = meta['versions']

    if need_version != '' and not need_version in versions:
        env['MLC_GIT_CHECKOUT'] = need_version

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    automotive_root = env['MLC_MLPERF_AUTOMOTIVE_SOURCE']
    env['MLC_MLPERF_AUTOMOTIVE_BEVFORMER_PATH'] = os.path.join(
        automotive_root, 'camera-3d-detection')
    env['MLC_MLPERF_AUTOMOTIVE_SSD_RESNET50_PATH'] = os.path.join(
        automotive_root, '2d-object-detection')
    env['MLC_MLPERF_AUTOMOTIVE_DEEPLABV3PLUS_PATH'] = os.path.join(
        automotive_root, 'semantic-segmentation')

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = automotive_root

#        20221024: we save and restore env in the main script and can clean env here for determinism
#    if '+PYTHONPATH' not in env: env['+PYTHONPATH'] = []
    env['+PYTHONPATH'] = []

    if os.path.exists(os.path.join(automotive_root, "loadgen", "VERSION.txt")):
        with open(os.path.join(automotive_root, "loadgen", "VERSION.txt")) as f:
            version_info = f.read().strip()
        env['MLC_MLPERF_AUTOMOTIVE_SOURCE_VERSION'] = version_info

    if is_true(env.get('MLC_GET_MLPERF_IMPLEMENTATION_ONLY', '')):
        return {'return': 0}

    env['MLC_MLPERF_AUTOMOTIVE_CONF_PATH'] = os.path.join(
        automotive_root, 'mlperf.conf')
    env['+PYTHONPATH'].append(
        os.path.join(
            env['MLC_MLPERF_AUTOMOTIVE_SOURCE'],
            'tools',
            'submission'))

    # To be uncommented after Pablo's PR is merged: https://github.com/mlcommons/mlperf_automotive/pull/14
    # valid_models = get_valid_models(
    #     env['MLC_MLPERF_LAST_RELEASE'],
    #     env['MLC_MLPERF_AUTOMOTIVE_SOURCE'])

    # state['MLC_MLPERF_AUTOMOTIVE_MODELS'] = valid_models

    if env.get('MLC_GIT_REPO_CURRENT_HASH', '') != '':
        env['MLC_VERSION'] += "-git-" + env['MLC_GIT_REPO_CURRENT_HASH']

    return {'return': 0, 'version': env['MLC_VERSION']}


def get_valid_models(mlperf_version, mlperf_path):

    import sys

    submission_checker_dir = os.path.join(mlperf_path, "tools", "submission")

    sys.path.append(submission_checker_dir)

    if not os.path.exists(os.path.join(
            submission_checker_dir, "submission_checker.py")):
        shutil.copy(os.path.join(submission_checker_dir, "submission-checker.py"), os.path.join(submission_checker_dir,
                                                                                                "submission_checker.py"))

    import submission_checker as checker

    config = checker.MODEL_CONFIG

    valid_models = config[mlperf_version]["models"]

    return valid_models
