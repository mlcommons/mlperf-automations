from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    if env.get('MLC_DUMP_RAW_PIP_FREEZE_FILE_PATH', '') == '':
        env['MLC_DUMP_RAW_PIP_FREEZE_FILE_PATH'] = os.path.join(
            os.getcwd(), "tmp-pip-freeze")

    quiet = is_true(env.get('MLC_QUIET', False))

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    automation = i['automation']

    pip_freeze = {}
    pip_freeze_file = env['MLC_DUMP_RAW_PIP_FREEZE_FILE_PATH']
    if not os.path.isfile(pip_freeze_file):
        # If was not created, sometimes issues on Windows
        # There is another workaround
        if os_info['platform'] == 'windows':
            r = automation.action_object.access({'action': 'system',
                                                 'automation': 'utils',
                                                 'cmd': 'py -m pip freeze',
                                                 'stdout': pip_freeze_file})
            # skip output

    if os.path.isfile(pip_freeze_file):
        with open(pip_freeze_file, "r") as f:
            for line in f.readlines():
                if "==" in line:
                    split = line.split("==")
                    pip_freeze[split[0]] = split[1].strip()

    state['pip_freeze'] = pip_freeze

    return {'return': 0}
