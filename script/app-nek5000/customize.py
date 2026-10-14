from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Nek5000 builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_NEK5000_SRC_PATH', '')
    bin_dir = os.path.join(src_path, 'bin')

    binary = os.path.join(bin_dir, 'genmap')
    if not os.path.isfile(binary):
        return {'return': 1,
                'error': f'Nek5000 tool (genmap) not found in {bin_dir}'}

    env['MLC_NEK5000_INSTALL_PATH'] = src_path
    env['MLC_NEK5000_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]

    return {'return': 0}
