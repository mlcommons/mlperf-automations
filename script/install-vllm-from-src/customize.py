from mlc import utils
import os
from utils import is_true


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    if not env.get('+ CFLAGS', []):
        env['+ CFLAGS'] = []
    if not env.get('+ CXXFLAGS', []):
        env['+ CXXFLAGS'] = []

    env['+ CFLAGS'] += ["-Wno-error=uninitialized",
                        "-Wno-error=maybe-uninitialized", "-fno-strict-aliasing"]
    env['+ CXXFLAGS'] += ["-Wno-error=uninitialized",
                          "-Wno-error=maybe-uninitialized", "-fno-strict-aliasing"]
    automation = i['automation']

    recursion_spaces = i['recursion_spaces']

    extra = ""

    if (pip_version and len(pip_version) > 1 and int(pip_version[0]) >= 23):
        extra += " --break-system-packages"

    if env.get('MLC_TMP_DEVICE', '') == "cpu":
        cmd = f"""pip3 install -r requirements/cpu.txt {extra} && VLLM_TARGET_DEVICE=cpu pip install {extra} . --no-build-isolation"""

    env['MLC_RUN_CMD'] = cmd

    return {'return': 0}
