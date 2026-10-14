from mlc import utils
import os
import glob


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Castro builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_CASTRO_SRC_PATH', '')
    compiler_tag = env.get('MLC_COMPILER_FAMILY', '') or 'default'
    hits = glob.glob(
        os.path.join(
            src_path,
            'install-' +
            compiler_tag,
            'bin',
            '*.ex'))
    if not hits:
        return {'return': 1, 'error': f'Castro executable not found under {src_path}'}
    bin_dir = os.path.dirname(hits[0])
    env['MLC_CASTRO_INSTALL_PATH'] = src_path
    env['MLC_CASTRO_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
