from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for E3SM builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_E3SM_SRC_PATH', '')
    install_dir = os.path.join(src_path, 'install')
    env['MLC_E3SM_INSTALL_PATH'] = install_dir
    bin_dir = os.path.join(install_dir, 'bin')
    env['MLC_E3SM_BIN_PATH'] = bin_dir if os.path.isdir(bin_dir) else src_path
    if os.path.isdir(bin_dir):
        env['+PATH'] = [bin_dir]
    return {'return': 0}
