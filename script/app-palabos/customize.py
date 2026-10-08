from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Palabos builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_PALABOS_SRC_PATH', '')
    binary = os.path.join(
        src_path,
        'examples',
        'showCases',
        'cavity3d',
        'cavity3d')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'Palabos binary not found at {binary}'}
    bin_dir = os.path.dirname(binary)
    env['MLC_PALABOS_INSTALL_PATH'] = src_path
    env['MLC_PALABOS_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
