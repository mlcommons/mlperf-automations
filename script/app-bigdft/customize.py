from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for BigDFT builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_BIGDFT_SRC_PATH', '')
    env['MLC_BIGDFT_INSTALL_PATH'] = src_path
    env['MLC_BIGDFT_BIN_PATH'] = src_path
    return {'return': 0}
