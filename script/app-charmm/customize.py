from mlc import utils
import os
import glob


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for CHARMM builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_CHARMM_SRC_PATH', '')
    env['MLC_CHARMM_INSTALL_PATH'] = src_path
    env['MLC_CHARMM_BIN_PATH'] = src_path
    return {'return': 0}
