from cmind import utils
import os
import sys


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = (env.get('CM_QUIET', False) == 'yes')

    utils_path = env['CM_TMP_CURRENT_SCRIPT_PATH']

    env['+PYTHONPATH'] = [utils_path]

    submission_checker_dir = os.path.join(
        env['CM_MLPERF_INFERENCE_SOURCE'], "tools", "submission")

    sys.path.append(submission_checker_dir)
    sys.path.append(utils_path)

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
