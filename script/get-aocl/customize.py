from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_AOCL_SRC_PATH'] = env['MLC_GIT_REPO_CHECKOUT_PATH']
    env['MLC_AOCL_BUILD_PATH'] = os.path.join(
        env['MLC_GIT_REPO_CHECKOUT_PATH'], "build")
    aocl_lib_path = os.path.join(
        env['MLC_GIT_REPO_CHECKOUT_PATH'],
        "build",
        "aocl-release",
        "src")
    env['MLC_AOCL_LIB_PATH'] = aocl_lib_path
    env['+LIBRARY_PATH'] = [aocl_lib_path] if '+LIBRARY_PATH' not in env else env['+LIBRARY_PATH'] + [aocl_lib_path]
    env['+LD_LIBRARY_PATH'] = [aocl_lib_path] if '+LD_LIBRARY_PATH' not in env else env['+LD_LIBRARY_PATH'] + [aocl_lib_path]

    return {'return': 0}
