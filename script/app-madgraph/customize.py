from mlc import utils
import os
import glob


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for MadGraph5_aMC@NLO builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_MADGRAPH_SRC_PATH', '')
    env['MLC_MADGRAPH_INSTALL_PATH'] = src_path
    env['MLC_MADGRAPH_BIN_PATH'] = src_path
    return {'return': 0}
