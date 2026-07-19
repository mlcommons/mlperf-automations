from mlc import utils
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}
    env = i['env']
    if 'MLC_GIT_DEPTH' not in env:
        env['MLC_GIT_DEPTH'] = ''
    if 'MLC_GIT_RECURSE_SUBMODULES' not in env:
        env['MLC_GIT_RECURSE_SUBMODULES'] = ''

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']
    env['CMSIS_PATH'] = os.path.join(os.getcwd(), 'cmsis')

    return {'return': 0}
