from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for HMMER builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_HMMER_SRC_PATH', '')
    install_dir = os.path.join(src_path, 'install')
    bin_dir = os.path.join(install_dir, 'bin')

    hmmsearch_bin = os.path.join(bin_dir, 'hmmsearch')
    if not os.path.isfile(hmmsearch_bin):
        return {'return': 1, 'error': f'HMMER binary (hmmsearch) not found in {bin_dir}'}

    env['MLC_HMMER_BIN_PATH'] = bin_dir
    env['MLC_HMMER_INSTALL_PATH'] = install_dir
    env['+PATH'] = [bin_dir]

    return {'return': 0}
