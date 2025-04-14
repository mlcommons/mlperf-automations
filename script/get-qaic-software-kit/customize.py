from mlc import utils
import os
from utils import is_true

def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    env['MLC_QAIC_SOFTWARE_KIT_PATH'] = env['MLC_GIT_CHECKOUT_PATH']

    quiet = is_true(env.get('MLC_QUIET', False))

    if env.get('+ CXXFLAGS', []) == []:
        env['+ CXXFLAGS'] = []
    if env.get('+ CFLAGS', []) == []:
        env['+ CFLAGS'] = []

    if env.get('MLC_LLVM_CLANG_VERSION', '') != '':
        clang_version_split = env['MLC_LLVM_CLANG_VERSION'].split(".")
        clang_major_version = int(clang_version_split[0])

        if clang_major_version >= 17:
            env['+ CFLAGS'].append("-Wno-error=c2x-extensions")

        if clang_major_version >= 16:
            env['+ CFLAGS'].append("-Wno-error=unused-but-set-variable")
            env['+ CXXFLAGS'].append("-Wno-error=unused-but-set-variable")

        if clang_major_version >= 13:
            env['+ CFLAGS'].append("-Wno-error=unused-const-variable")
            env['+ CFLAGS'].append("-Wno-error=unused-but-set-variable")
            env['+ CFLAGS'].append("-Wno-error=strict-prototypes")
            env['+ CFLAGS'].append("-Wno-error=unused-variable")
            env['+ CXXFLAGS'].append("-Wno-error=unused-const-variable")
            env['+ CXXFLAGS'].append("-Wno-error=unused-variable")
            env['+ CXXFLAGS'].append("-Wno-error=unused-private-field")
            env['+ CXXFLAGS'].append("-Wno-error=unused-result")
            env['+ CXXFLAGS'].append("-Wno-error=string-concatenation")
            env['+ CXXFLAGS'].append("-Wno-error=infinite-recursion")

        if clang_major_version == 12:
            env['+ CXXFLAGS'].append("-Wno-error=unknown-warning-option")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    env['MLC_QAIC_RUNNER_PATH'] = os.path.join(
        env['MLC_QAIC_SOFTWARE_KIT_PATH'], "build", "utils", "qaic-runner")

    if '+PATH' not in env:
        env['+PATH'] = []

    env['+PATH'].append(env['MLC_QAIC_RUNNER_PATH'])
    env['MLC_QAIC_RUNNER_PATH'] = os.path.join(
        env['MLC_QAIC_RUNNER_PATH'], "qaic-runner")

    return {'return': 0}
