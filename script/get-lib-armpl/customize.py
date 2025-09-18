from mlc import utils
import os


def preprocess(i):
    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']
    return {'return': 0}


def postprocess(i):

    env = i['env']

    paths = [
        "+C_INCLUDE_PATH",
        "+CPLUS_INCLUDE_PATH",
        "+LD_LIBRARY_PATH",
        "+DYLD_FALLBACK_LIBRARY_PATH"
    ]

    for key in paths:
        env[key] = []

    armpl_install_path = env.get(
        'MLC_EXTRACT_EXTRACTED_SUBDIR_PATH',
        env['MLC_ARMPL_INSTALL_PATH'])

    include_path = os.path.join(armpl_install_path, 'include')

    env['+C_INCLUDE_PATH'].append(inc_path)
    env['+CPLUS_INCLUDE_PATH'].append(inc_path)

    lib_path = os.path.join(armpl_install_path, 'lib')
    env['+LD_LIBRARY_PATH'].append(lib_path)
    env['+DYLD_FALLBACK_LIBRARY_PATH'].append(lib_path)

    env['MLC_ARMPL_INCLUDE_PATH'] = include_path
    env['MLC_ARMPL_LIB_PATH'] = lib_path

    return {'return': 0}
