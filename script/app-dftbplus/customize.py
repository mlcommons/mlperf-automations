from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for DFTB+ builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_DFTBPLUS_SRC_PATH', '')
    binary = os.path.join(src_path, '_build', 'app', 'dftb+', 'dftb+')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'DFTB+ binary not found at {binary}'}
    bin_dir = os.path.dirname(binary)
    env['MLC_DFTBPLUS_INSTALL_PATH'] = src_path
    env['MLC_DFTBPLUS_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
