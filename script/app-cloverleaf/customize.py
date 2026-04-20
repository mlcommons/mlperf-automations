from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for CloverLeaf builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_CLOVERLEAF_SRC_PATH', '')
    install_dir = os.path.join(src_path, 'install')
    bin_dir = os.path.join(install_dir, 'bin')

    clover_bin = os.path.join(bin_dir, 'clover_leaf')
    if not os.path.isfile(clover_bin):
        # Try source directory
        clover_bin = os.path.join(src_path, 'clover_leaf')
        if not os.path.isfile(clover_bin):
            return {'return': 1, 'error': f'CloverLeaf binary not found in {bin_dir} or {src_path}'}
        bin_dir = src_path

    env['MLC_CLOVERLEAF_BIN_PATH'] = bin_dir
    env['MLC_CLOVERLEAF_INSTALL_PATH'] = install_dir
    env['+PATH'] = [bin_dir]

    return {'return': 0}
