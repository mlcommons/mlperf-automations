from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Yambo builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_YAMBO_SRC_PATH', '')
    env['MLC_YAMBO_INSTALL_PATH'] = src_path
    env['MLC_YAMBO_BIN_PATH'] = src_path
    return {'return': 0}
