from mlc import utils
import os
import glob


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for FV3 builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_FV3_SRC_PATH', '')
    env['MLC_FV3_INSTALL_PATH'] = src_path
    env['MLC_FV3_BIN_PATH'] = src_path
    return {'return': 0}
