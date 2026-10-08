from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for bwa-mem2 builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_BWA_MEM2_SRC_PATH', '')
    install_dir = os.path.join(src_path, 'install')
    bin_dir = os.path.join(install_dir, 'bin')

    binary = os.path.join(bin_dir, 'bwa-mem2')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'bwa-mem2 binary not found in {bin_dir}'}

    env['MLC_BWA_MEM2_INSTALL_PATH'] = install_dir
    env['MLC_BWA_MEM2_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]

    return {'return': 0}
