from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Athena++ builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_ATHENA_SRC_PATH', '')
    bin_dir = os.path.join(src_path, 'bin')

    binary = os.path.join(bin_dir, 'athena')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'Athena++ binary not found in {bin_dir}'}

    env['MLC_ATHENA_INSTALL_PATH'] = src_path
    env['MLC_ATHENA_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]

    return {'return': 0}
