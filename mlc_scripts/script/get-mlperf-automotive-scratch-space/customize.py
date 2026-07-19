from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    if env.get('MLC_ABTF_SCRATCH_PATH', '') == '':
        env['MLC_ABTF_SCRATCH_PATH'] = os.getcwd()

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_ABTF_SCRATCH_PATH_MODELS'] = os.path.join(
        env['MLC_ABTF_SCRATCH_PATH'], "models")
    env['MLC_ABTF_SCRATCH_PATH_DATASETS'] = os.path.join(
        env['MLC_ABTF_SCRATCH_PATH'], "datasets")

    if not os.path.exists(env['MLC_ABTF_SCRATCH_PATH_MODELS']):
        os.makedirs(env['MLC_ABTF_SCRATCH_PATH_MODELS'])

    if not os.path.exists(env['MLC_ABTF_SCRATCH_PATH_DATASETS']):
        os.makedirs(env['MLC_ABTF_SCRATCH_PATH_DATASETS'])

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_ABTF_SCRATCH_PATH']

    return {'return': 0}
