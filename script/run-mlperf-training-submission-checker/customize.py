from mlc import utils
import os
import subprocess


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    submission_dir = env.get("MLC_MLPERF_SUBMISSION_DIR", "")

    version = env.get('MLC_MLPERF_SUBMISSION_CHECKER_VERSION', 'v3.1')

    if submission_dir == "":
        return {'return': 1, 'error': 'Please set MLC_MLPERF_SUBMISSION_DIR'}

    submitter = env.get("MLC_MLPERF_SUBMITTER", "")  # "default")
    if ' ' in submitter:
        return {
            'return': 1, 'error': 'MLC_MLPERF_SUBMITTER cannot contain a space. Please provide a name without space using --submitter input. Given value: {}'.format(submitter)}

    submission_checker_file = os.path.join(
        env['MLC_MLPERF_LOGGING_REPO_PATH'],
        "scripts",
        "verify_for_" + version + "_training.sh")

    extra_args = ' ' + env.get('MLC_MLPERF_SUBMISSION_CHECKER_EXTRA_ARGS', '')

    CMD = submission_checker_file + " " + submission_dir

    env['MLC_RUN_CMD'] = CMD

    return {'return': 0}


def postprocess(i):

    env = i['env']
    if env.get('MLC_TAR_SUBMISSION_DIR'):
        env['MLC_TAR_INPUT_DIR'] = env.get(
            'MLC_MLPERF_SUBMISSION_DIR', '$HOME')

    return {'return': 0}
