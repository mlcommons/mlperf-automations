from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_AOCL_LIBM_SRC_PATH', env.get('MLC_GIT_REPO_CHECKOUT_PATH', ''))
    env['MLC_AOCL_LIBM_SRC_PATH'] = src_path
    env['MLC_AOCL_LIBM_BUILD_PATH'] = os.path.join(src_path, 'build')

    aocl_lib_path = os.path.join(src_path, 'build', 'aocl-release', 'src')
    env['MLC_AOCL_LIBM_LIB_PATH'] = aocl_lib_path

    env['+LIBRARY_PATH'] = [aocl_lib_path]
    env['+LD_LIBRARY_PATH'] = [aocl_lib_path]

    return {'return': 0}
