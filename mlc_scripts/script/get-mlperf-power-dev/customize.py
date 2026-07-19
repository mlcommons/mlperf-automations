from mlc import utils
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    return {'return': 0}


def postprocess(i):

    env = i['env']
    if env.get('MLC_VERSION', '') == '':
        env['MLC_VERSION'] = "master"

    if env.get('MLC_GIT_REPO_CURRENT_HASH', '') != '':
        env['MLC_VERSION'] += "-git-" + env['MLC_GIT_REPO_CURRENT_HASH']

    return {'return': 0, 'version': env['MLC_VERSION']}
