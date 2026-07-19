from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    env['MLC_BLIS_SRC_PATH'] = env['MLC_GIT_CHECKOUT_PATH']

    return {'return': 0}


def postprocess(i):

    env = i['env']
    install_dir = os.path.join(env['MLC_BLIS_SRC_PATH'], "install")

    env['MLC_BLIS_INSTALL_PATH'] = install_dir
    env['MLC_BLIS_INC'] = os.path.join(install_dir, 'include', 'blis')
    env['MLC_BLIS_LIB'] = os.path.join(install_dir, 'lib', 'libblis.a')

    blis_lib_path = os.path.join(install_dir, 'lib')

    env['+LD_LIBRARY_PATH'] = [blis_lib_path] if '+LD_LIBRARY_PATH' not in env else env['+LD_LIBRARY_PATH'] + [blis_lib_path]

    return {'return': 0}
