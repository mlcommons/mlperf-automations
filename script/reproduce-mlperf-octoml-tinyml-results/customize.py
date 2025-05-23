from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    if 'MLC_MICROTVM_VARIANT' not in env:
        env['MLC_MICROTVM_VARIANT'] = 'microtvm_cmsis_nn'
    if 'MLC_TINY_MODEL' not in env:
        env['MLC_TINY_MODEL'] = 'ic'

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}
    env['+C_INCLUDE_PATH'] = []
    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
