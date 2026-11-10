from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported'}
    env = i['env']
    if env.get('MLC_HOST_PLATFORM_FLAVOR', '') not in ('', 'x86_64'):
        return {'return': 1, 'error': 'AOCL-FFTW is x86_64-only; use get,lib,fftw3'}
    if not env.get('MLC_AOCL_FFTW_SRC_PATH'):
        env['MLC_AOCL_FFTW_SRC_PATH'] = env.get('MLC_GIT_REPO_CHECKOUT_PATH', '')
    env['MLC_AOCL_FFTW_INSTALL_PATH'] = os.path.join(os.getcwd(), 'install')
    return {'return': 0}


def postprocess(i):
    env = i['env']
    prefix = env['MLC_AOCL_FFTW_INSTALL_PATH']
    lib = os.path.join(prefix, 'lib')
    if not os.path.isdir(lib):
        lib = os.path.join(prefix, 'lib64')
    env['MLC_AOCL_FFTW_LIB_PATH'] = lib
    env['MLC_AOCL_FFTW_VERSION'] = env.get(
        'MLC_AOCL_FFTW_VERSION', env.get('MLC_GIT_CHECKOUT_TAG', ''))
    inc = os.path.join(prefix, 'include')
    env['+LD_LIBRARY_PATH'] = [lib]
    env['+LIBRARY_PATH'] = [lib]
    env['+C_INCLUDE_PATH'] = [inc]
    env['+CPLUS_INCLUDE_PATH'] = [inc]
    env['+PKG_CONFIG_PATH'] = [os.path.join(lib, 'pkgconfig')]
    env['+CMAKE_PREFIX_PATH'] = [prefix]
    env['MLC_DEPENDENT_CACHED_PATH'] = prefix
    return {'return': 0}
