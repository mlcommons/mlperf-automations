from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    if is_true(env.get('MLC_AOCL_BINARY_DOWNLOAD', '')):
        if not is_true(env.get('MLC_AOCL_ACCEPT_EULA', '')):
            return {'return': 1, 'error': 'You must accept the AMD EULA to download binary packages. Use --accept_eula=yes to accept.'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if is_true(env.get('MLC_AOCL_BINARY_DOWNLOAD', '')):
        install_path = env.get('MLC_AOCL_DA_BINARY_PATH', '')
        if not install_path:
            return {'return': 1, 'error': 'Binary download path not set'}
        # Find the library subdirectory inside the extracted archive
        for entry in os.listdir(install_path):
            entry_path = os.path.join(install_path, entry)
            if os.path.isdir(entry_path) and (os.path.isdir(os.path.join(entry_path, 'lib')) or os.path.isdir(os.path.join(entry_path, 'lib64'))):
                install_path = entry_path
                break
        # Find the library subdirectory inside the extracted archive
        for entry in os.listdir(install_path):
            entry_path = os.path.join(install_path, entry)
            if os.path.isdir(entry_path) and (os.path.isdir(os.path.join(entry_path, 'lib')) or os.path.isdir(os.path.join(entry_path, 'lib64'))):
                install_path = entry_path
                break
    else:
        src_path = env.get('MLC_AOCL_DA_SRC_PATH', env.get('MLC_GIT_REPO_CHECKOUT_PATH', ''))
        env['MLC_AOCL_DA_SRC_PATH'] = src_path
        env['MLC_AOCL_DA_BUILD_PATH'] = os.path.join(src_path, 'build')
        install_path = os.path.join(src_path, 'install')

    env['MLC_AOCL_DA_INSTALL_PATH'] = install_path
    env['MLC_AOCL_BINARY_INSTALL_PATH'] = install_path

    lib_path = os.path.join(install_path, 'lib')
    if not os.path.isdir(lib_path):
        lib_path = os.path.join(install_path, 'lib64')
    env['MLC_AOCL_DA_LIB_PATH'] = lib_path

    env['+LD_LIBRARY_PATH'] = [lib_path]
    env['+LIBRARY_PATH'] = [lib_path]
    env['+C_INCLUDE_PATH'] = [os.path.join(install_path, 'include')]
    env['+CPLUS_INCLUDE_PATH'] = [os.path.join(install_path, 'include')]

    return {'return': 0}
