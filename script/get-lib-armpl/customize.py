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
    print(env)
    return {'return': 1}

    paths = [
        "+C_INCLUDE_PATH",
        "+CPLUS_INCLUDE_PATH",
        "+LD_LIBRARY_PATH",
        "+DYLD_FALLBACK_LIBRARY_PATH"
    ]

    for key in paths:
        env[key] = []

    include_paths = []
    armpl_src_path = env['MLC_ARMPL_SRC_PATH']
    armpl_lib_path = os.path.join(
        armpl_src_path,
        env['MLC_ARMPL_TAR_FILENAME'])
    include_paths.append(os.path.join(os.getcwd(), 'include'))
    include_paths.append(os.path.join(armnn_src_path, 'include'))
    include_paths.append(os.path.join(armnn_src_path, 'profiling'))

    for inc_path in include_paths:
        env['+C_INCLUDE_PATH'].append(inc_path)
        env['+CPLUS_INCLUDE_PATH'].append(inc_path)

    lib_path = os.path.join(os.getcwd())
    env['+LD_LIBRARY_PATH'].append(lib_path)
    env['+DYLD_FALLBACK_LIBRARY_PATH'].append(lib_path)

    return {'return': 1}
