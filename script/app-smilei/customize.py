from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Smilei builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_SMILEI_SRC_PATH', '')
    compiler_tag = env.get('MLC_COMPILER_FAMILY', '') or 'default'
    binary = os.path.join(src_path, 'install-' + compiler_tag, 'bin', 'smilei')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'Smilei binary not found at {binary}'}
    env['MLC_SMILEI_INSTALL_PATH'] = os.path.join(
        src_path, 'install-' + compiler_tag)
    env['MLC_SMILEI_BIN_PATH'] = os.path.join(
        src_path, 'install-' + compiler_tag, 'bin')
    env['+PATH'] = [src_path]
    return {'return': 0}
