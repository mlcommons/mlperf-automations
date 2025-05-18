from mlc import utils
import os
from utils import is_true


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    cmd = "gh auth login"
    if env.get('MLC_GH_AUTH_TOKEN', '') != '':
        if os_info['platform'] == 'windows':
            with open("token", "w") as f:
                f.write(env['MLC_GH_AUTH_TOKEN'])
            cmd = f"{cmd} --with-token < token"
        else:
            cmd = f" echo {env['MLC_GH_AUTH_TOKEN']} | {cmd} --with-token"

    env['MLC_RUN_CMD'] = cmd
    quiet = is_true(env.get('MLC_QUIET', False))

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
