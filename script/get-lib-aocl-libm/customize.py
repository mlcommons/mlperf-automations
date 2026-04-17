from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    if env.get('MLC_AOCL_BINARY_DOWNLOAD') == 'yes':
        if env.get('MLC_AOCL_ACCEPT_EULA') != 'yes':
            return {'return': 1, 'error': 'You must accept the AMD EULA to download binary packages. Use --accept_eula=yes to accept.'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_AOCL_BINARY_DOWNLOAD') == 'yes':
        install_path = env.get('MLC_AOCL_LIBM_BINARY_PATH', '')
        if not install_path:
            return {'return': 1, 'error': 'Binary download path not set'}
    else:
        src_path = env.get('MLC_AOCL_LIBM_SRC_PATH', env.get('MLC_GIT_REPO_CHECKOUT_PATH', ''))
        env['MLC_AOCL_LIBM_SRC_PATH'] = src_path
        env['MLC_AOCL_LIBM_BUILD_PATH'] = os.path.join(src_path, 'build')
        install_path = os.path.join(src_path, 'build', 'aocl-release', 'src')

    env['MLC_AOCL_LIBM_INSTALL_PATH'] = install_path
    env['MLC_AOCL_BINARY_INSTALL_PATH'] = install_path

    aocl_lib_path = install_path
    if env.get('MLC_AOCL_BINARY_DOWNLOAD') == 'yes':
        lib_path = os.path.join(install_path, 'lib')
        if not os.path.isdir(lib_path):
            lib_path = os.path.join(install_path, 'lib64')
        aocl_lib_path = lib_path
    env['MLC_AOCL_LIBM_LIB_PATH'] = aocl_lib_path

    env['+LIBRARY_PATH'] = [aocl_lib_path]
    env['+LD_LIBRARY_PATH'] = [aocl_lib_path]

    if env.get('MLC_AOCL_BINARY_DOWNLOAD') == 'yes':
        env['+C_INCLUDE_PATH'] = [os.path.join(install_path, 'include')]
        env['+CPLUS_INCLUDE_PATH'] = [os.path.join(install_path, 'include')]

    return {'return': 0}
