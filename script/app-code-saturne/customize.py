from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1,
                'error': 'Windows is not supported for code_saturne builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_CODE_SATURNE_SRC_PATH', '')
    binary = os.path.join(src_path, 'install/bin/code_saturne')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'code_saturne binary not found at {binary}'}
    bin_dir = os.path.dirname(binary)
    env['MLC_CODE_SATURNE_INSTALL_PATH'] = os.path.join(src_path, 'install')
    env['MLC_CODE_SATURNE_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
