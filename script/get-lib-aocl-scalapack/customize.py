from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_AOCL_SCALAPACK_SRC_PATH', env.get('MLC_GIT_REPO_CHECKOUT_PATH', ''))
    install_path = os.path.join(src_path, 'install')

    env['MLC_AOCL_SCALAPACK_SRC_PATH'] = src_path
    env['MLC_AOCL_SCALAPACK_BUILD_PATH'] = os.path.join(src_path, 'build')
    env['MLC_AOCL_SCALAPACK_INSTALL_PATH'] = install_path

    lib_path = os.path.join(install_path, 'lib')
    if not os.path.isdir(lib_path):
        lib_path = os.path.join(install_path, 'lib64')
    env['MLC_AOCL_SCALAPACK_LIB_PATH'] = lib_path

    env['+LD_LIBRARY_PATH'] = [lib_path]
    env['+LIBRARY_PATH'] = [lib_path]
    env['+C_INCLUDE_PATH'] = [os.path.join(install_path, 'include')]
    env['+CPLUS_INCLUDE_PATH'] = [os.path.join(install_path, 'include')]

    return {'return': 0}
