from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Enzo builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_ENZO_SRC_PATH', '')
    compiler_tag = env.get('MLC_COMPILER_FAMILY', '') or 'default'
    bin_dir = os.path.join(src_path, 'install-' + compiler_tag, 'bin')

    binary = os.path.join(bin_dir, 'enzo.exe')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'Enzo binary (enzo.exe) not found in {bin_dir}'}

    env['MLC_ENZO_INSTALL_PATH'] = src_path
    env['MLC_ENZO_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]

    return {'return': 0}
