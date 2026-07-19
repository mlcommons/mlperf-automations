from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']
    env['OMP_PROC_BIND'] = 'true'

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
