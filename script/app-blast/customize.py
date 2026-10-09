from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for BLAST+ builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_BLAST_SRC_PATH', '')
    install_dir = os.path.join(src_path, 'install')
    bin_dir = os.path.join(install_dir, 'bin')

    binary = os.path.join(bin_dir, 'blastn')
    if not os.path.isfile(binary):
        return {'return': 1,
                'error': f'BLAST+ binary (blastn) not found in {bin_dir}'}

    env['MLC_BLAST_INSTALL_PATH'] = install_dir
    env['MLC_BLAST_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]

    return {'return': 0}
