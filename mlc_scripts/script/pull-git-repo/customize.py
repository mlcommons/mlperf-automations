from mlc import utils
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

    env = i['env']
    meta = i['meta']

    if 'MLC_GIT_CHECKOUT_PATH' not in env:
        return {'return': 1, 'error': 'MLC_GIT_CHECKOUT_PATH is not set'}

    env['MLC_GIT_PULL_CMD'] = "git pull --rebase"

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    return {'return': 0}
