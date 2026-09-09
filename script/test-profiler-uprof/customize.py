from mlc import utils
import os


def preprocess(i):
    env = i['env']
    if env.get('MLC_UPROF_BIN_WITH_PATH', '') == '':
        return {'return': 1, 'error': 'MLC_UPROF_BIN_WITH_PATH not set; get,profiler,uprof must run first'}
    return {'return': 0}


def postprocess(i):
    return {'return': 0}
