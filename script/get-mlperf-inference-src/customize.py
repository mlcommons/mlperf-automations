from mlc import utils
from utils import is_true
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

#    if os_info['platform'] == 'windows':
# return {'return':1, 'error': 'Windows is not supported in this script
# yet'}

    env = i['env']
    meta = i['meta']

    script_path = i['run_script_input']['path']

    if env.get('MLC_GIT_CHECKOUT', '') == '' and env.get(
            'MLC_GIT_URL', '') == '' and env.get('MLC_VERSION', '') == '':
        # if custom checkout and url parameters are not set and MLC_VERSION is
        # not specified
        env['MLC_VERSION'] = "master"
        env["MLC_GIT_CHECKOUT"] = "master"
        env["MLC_GIT_URL"] = "https://github.com/mlcommons/inference"
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
            env["MLC_GIT_URL"] = "https://github.com/mlcommons/inference"

    if env.get("MLC_MLPERF_LAST_RELEASE", '') == '':
        env["MLC_MLPERF_LAST_RELEASE"] = "v5.0"

    if 'MLC_GIT_DEPTH' not in env:
        env['MLC_GIT_DEPTH'] = ''

    if 'MLC_GIT_RECURSE_SUBMODULES' not in env:
        env['MLC_GIT_RECURSE_SUBMODULES'] = ''
    submodules = []
    possible_submodules = {
        "gn": "third_party/gn",
        "pybind": "third_party/pybind",
        "deeplearningexamples": "language/bert/DeepLearningExamples",
        "3d-unet": "vision/medical_imaging/3d-unet-brats19/nnUnet"
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

    inference_root = env['MLC_MLPERF_INFERENCE_SOURCE']
    env['MLC_MLPERF_INFERENCE_VISION_PATH'] = os.path.join(
        inference_root, 'vision')
    env['MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH'] = os.path.join(
        inference_root, 'vision', 'classification_and_detection')
    env['MLC_MLPERF_INFERENCE_BERT_PATH'] = os.path.join(
        inference_root, 'language', 'bert')
    env['MLC_MLPERF_INFERENCE_GPTJ_PATH'] = os.path.join(
        inference_root, 'language', 'gpt-j')
    env['MLC_MLPERF_INFERENCE_RNNT_PATH'] = os.path.join(
        inference_root, 'speech_recognition', 'rnnt')
    env['MLC_MLPERF_INFERENCE_DLRM_PATH'] = os.path.join(
        inference_root, 'recommendation', 'dlrm')
    env['MLC_MLPERF_INFERENCE_DLRM_V2_PATH'] = os.path.join(
        inference_root, 'recommendation', 'dlrm_v2')
    env['MLC_MLPERF_INFERENCE_RGAT_PATH'] = os.path.join(
        inference_root, 'graph', 'R-GAT')
    env['MLC_MLPERF_INFERENCE_3DUNET_PATH'] = os.path.join(
        inference_root, 'vision', 'medical_imaging', '3d-unet-kits19')
    env['MLC_MLPERF_INFERENCE_POINTPAINTING_PATH'] = os.path.join(
        inference_root, 'automotive', '3d-object-detection')

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = inference_root

#        20221024: we save and restore env in the main script and can clean env here for determinism
#    if '+PYTHONPATH' not in env: env['+PYTHONPATH'] = []
    env['+PYTHONPATH'] = []
    env['+PYTHONPATH'].append(
        os.path.join(
            env['MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH'],
            'python'))

    if os.path.exists(os.path.join(inference_root, "loadgen", "VERSION.txt")):
        with open(os.path.join(inference_root, "loadgen", "VERSION.txt")) as f:
            version_info = f.read().strip()
        env['MLC_MLPERF_INFERENCE_SOURCE_VERSION'] = version_info

    if is_true(env.get('MLC_GET_MLPERF_IMPLEMENTATION_ONLY', '')):
        return {'return': 0}

    env['MLC_MLPERF_INFERENCE_CONF_PATH'] = os.path.join(
        inference_root, 'mlperf.conf')
    env['+PYTHONPATH'].append(
        os.path.join(
            env['MLC_MLPERF_INFERENCE_SOURCE'],
            'tools',
            'submission'))

    valid_models = get_valid_models(
        env['MLC_MLPERF_LAST_RELEASE'],
        env['MLC_MLPERF_INFERENCE_SOURCE'], env)

    state['MLC_MLPERF_INFERENCE_MODELS'] = valid_models

    if env.get('MLC_GIT_REPO_CURRENT_HASH', '') != '':
        env['MLC_VERSION'] += "-git-" + env['MLC_GIT_REPO_CURRENT_HASH']

    return {'return': 0, 'version': env['MLC_VERSION']}


def get_valid_models(mlperf_version, mlperf_path, env):

    import sys
    submission_checker_modularised = False  # for ensuring backward compatibility with the previous submission checker
    submission_checker_root = os.path.join(mlperf_path, "tools", "submission")

    if os.path.isdir(os.path.join(
            mlperf_path, "tools", "submission", "submission_checker")):
        submission_checker_dir = os.path.join(mlperf_path, "tools", "submission", "submission_checker")
        submission_checker_modularised = True
        env['MLC_MLPERF_MODULARISED_INFERENCE_SUBMISSION_CHECKER'] = 'yes'

    sys.path.append(submission_checker_root)

    if not submission_checker_modularised:
        if not os.path.exists(os.path.join(
                submission_checker_root, "submission_checker.py")):
            shutil.copy(os.path.join(submission_checker_root, "submission-checker.py"),
                        os.path.join(submission_checker_root, "submission_checker.py"))
        import submission_checker as checker
        config = checker.MODEL_CONFIG
    else:
        import submission_checker.main as checker
        import submission_checker.constants as constants
        config = constants.MODEL_CONFIG

    valid_models = config[mlperf_version]["models"]

    return valid_models
