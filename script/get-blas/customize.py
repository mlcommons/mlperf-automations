from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    env['MLC_BLAS_SRC_PATH'] = env['MLC_GIT_CHECKOUT_PATH']

    return {'return': 0}


def postprocess(i):

    env = i['env']
    install_dir = os.path.join(os.getcwd(), "install")

    env['MLC_BLAS_INSTALL_PATH'] = install_dir
    env['MLC_BLAS_INC'] = os.path.join(install_dir, 'include')
    env['MLC_BLAS_LIB'] = os.path.join(install_dir, 'lib', 'libopenblas.a')

    blas_lib_path = os.path.join(install_dir, 'lib')

    env['+LD_LIBRARY_PATH'] = [blas_lib_path] if '+LD_LIBRARY_PATH' not in env else env['+LD_LIBRARY_PATH'] + [blas_lib_path]

    return {'return': 0}
