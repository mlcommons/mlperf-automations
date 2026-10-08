from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for ROOT builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_ROOT_SRC_PATH', '')
    lib = os.path.join(src_path, 'build', 'lib', 'libCore.so')
    if not os.path.isfile(lib):
        return {'return': 1, 'error': f'ROOT core library not found at {lib}'}
    bin_dir = os.path.join(src_path, 'build', 'bin')
    env['MLC_ROOT_INSTALL_PATH'] = os.path.join(src_path, 'build')
    env['MLC_ROOT_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
