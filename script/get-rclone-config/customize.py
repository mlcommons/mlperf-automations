from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    run_cmds = []
    if env.get('MLC_RCLONE_CONFIG_CMD', '') != '':
        run_cmds.append(env['MLC_RCLONE_CONFIG_CMD'])

    if env.get('MLC_RCLONE_CONNECT_CMD', '') != '' and not is_true(
            env.get('MLC_BYPASS_RCLONE_AUTH', '')):
        run_cmds.append(env['MLC_RCLONE_CONNECT_CMD'])

    env['MLC_RUN_CMD'] = ' && '.join(run_cmds)

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
