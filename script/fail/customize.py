from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    # Checking conditions
    if is_true(env.get('MLC_FAIL_WINDOWS', '')):
        if os_info['platform'] == 'windows':
            return {'return': 1,
                    'error': 'MLC detected fail condition: running on Windows'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
