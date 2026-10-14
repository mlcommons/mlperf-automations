from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for SU2 builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_SU2_SRC_PATH', '')
    compiler_tag = env.get('MLC_COMPILER_FAMILY', '') or 'default'
    binary = os.path.join(
        src_path,
        'install-' +
        compiler_tag,
        'bin',
        'SU2_CFD')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'SU2 binary not found at {binary}'}
    bin_dir = os.path.dirname(binary)
    env['MLC_SU2_INSTALL_PATH'] = os.path.join(
        src_path, 'install-' + compiler_tag)
    env['MLC_SU2_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
