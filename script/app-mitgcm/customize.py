from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for MITgcm builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_MITGCM_SRC_PATH', '')
    compiler_tag = env.get('MLC_COMPILER_FAMILY', '') or 'default'
    binary = os.path.join(
        src_path,
        'verification/tutorial_barotropic_gyre',
        'build-' + compiler_tag,
        'mitgcmuv')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'MITgcm binary not found at {binary}'}
    bin_dir = os.path.dirname(binary)
    env['MLC_MITGCM_INSTALL_PATH'] = os.path.join(src_path, 'install')
    env['MLC_MITGCM_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
