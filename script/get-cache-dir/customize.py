from mlc import utils
import os
from utils import is_true


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    return {'return': 0}


def postprocess(i):

    env = i['env']

    cache_dir = os.getcwd()
    if env.get('MLC_CACHE_DIR_ENV_NAME', '') != '':
        env[env['MLC_CACHE_DIR_ENV_NAME']] = cache_dir

    env['MLC_CACHE_DIR'] = cache_dir
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = cache_dir

    return {'return': 0}
