from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    logger = i['automation'].logger

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    automation = i['automation']

    recursion_spaces = i['recursion_spaces']

    need_version = env.get('MLC_VERSION', '')
    if need_version == '':
        return {'return': 1,
                'error': 'internal problem - MLC_VERSION is not defined in env'}

    logger.info(f"{recursion_spaces}    # Requested version: {need_version}")

    path_bin = os.path.join(os.getcwd(), 'install', 'bin')

    env['MLC_PYTHON_INSTALLED_PATH'] = path_bin

    return {'return': 0}


def postprocess(i):

    env = i['env']
    variation_tags = i['variation_tags']

    path_lib = os.path.join(os.getcwd(), 'install', 'lib')
    env['+LD_LIBRARY_PATH'] = [path_lib]

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = os.getcwd()

    env['MLC_PYTHON_BIN_WITH_PATH'] = os.path.join(
        env['MLC_PYTHON_INSTALLED_PATH'], 'python3')

    # We don't need to check default paths here because we force install to
    # cache
    env['+PATH'] = [env['MLC_PYTHON_INSTALLED_PATH']]
    path_include = os.path.join(os.getcwd(), 'install', 'include')
    env['+C_INCLUDE_PATH'] = [path_include]

    return {'return': 0}
