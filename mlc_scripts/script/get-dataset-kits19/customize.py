from mlc import utils
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']
    meta = i['meta']

    if not env.get('MLC_GIT_CHECKOUT', ''):
        return {
            'return': 1, 'error': 'Please provide a valid MLC_GIT_SHA inside the custom variation of _cm.json'}

    if 'MLC_GIT_DEPTH' not in env:
        env['MLC_GIT_DEPTH'] = ''

    if 'MLC_GIT_RECURSE_SUBMODULES' not in env:
        env['MLC_GIT_RECURSE_SUBMODULES'] = ''

    need_version = env.get('MLC_VERSION', '')
    versions = meta['versions']

    if need_version != '' and not need_version in versions:
        env['MLC_GIT_CHECKOUT'] = need_version

    return {'return': 0}


def postprocess(i):

    env = i['env']
    env['MLC_DATASET_PATH'] = os.path.join(os.getcwd(), 'kits19', 'data')
    state = i['state']

    return {'return': 0}
