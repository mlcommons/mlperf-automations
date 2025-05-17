from mlc import utils
from utils import is_true
import os
import sys


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    utils_path = env['MLC_TMP_CURRENT_SCRIPT_PATH']

    env['+PYTHONPATH'] = [utils_path]

    submission_checker_dir = os.path.join(
        env['MLC_MLPERF_AUTOMOTIVE_SOURCE'], "tools", "submission")

    sys.path.append(submission_checker_dir)
    sys.path.append(utils_path)

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
