from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    cmds = []

    if env.get('MLC_ULIMIT_NOFILE', '') != '':
        cmds.append(f"ulimit -n {env['MLC_ULIMIT_NOFILE']}")

    env['MLC_RUN_CMD'] = " && ".join(cmds)

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
