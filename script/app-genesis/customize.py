from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for GENESIS builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_GENESIS_SRC_PATH', '')
    compiler_tag = env.get('MLC_COMPILER_FAMILY', '') or 'default'
    binary = os.path.join(src_path, 'install-' + compiler_tag, 'bin', 'atdyn')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'GENESIS binary not found at {binary}'}
    bin_dir = os.path.dirname(binary)
    env['MLC_GENESIS_INSTALL_PATH'] = os.path.join(src_path, 'install-' + compiler_tag)
    env['MLC_GENESIS_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
