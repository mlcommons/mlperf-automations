from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    if env.get('MLC_MLPERF_INFERENCE_SUBMISSION_DIR', '') == '':
        if not os.path.exists("mlperf-inference-submission"):
            os.mkdir("mlperf-inference-submission")
        env['MLC_MLPERF_INFERENCE_SUBMISSION_DIR'] = os.path.join(
            os.getcwd(), "mlperf-inference-submission")

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_MLPERF_INFERENCE_SUBMISSION_DIR']

    return {'return': 0}
