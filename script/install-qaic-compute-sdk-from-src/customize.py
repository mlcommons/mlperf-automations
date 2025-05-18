from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    env['MLC_QAIC_COMPUTE_SDK_PATH'] = env['MLC_GIT_CHECKOUT_PATH']

    '''
    if env.get('+PATH', []) == []:
        env['+PATH'] = []
    env['+PATH'].append(env['MLC_LLVM_INSTALLED_PATH'])

    if env.get('+LD_LIBRARY_PATH', []) == []:
        env['+LD_LIBRARY_PATH'] = []
    env['+LD_LIBRARY_PATH'].append(os.path.join(env['MLC_LLVM_INSTALLED_PATH'], "..", "lib"))
    '''
    quiet = is_true(env.get('MLC_QUIET', False))

    return {'return': 0}


def postprocess(i):

    env = i['env']
    # env['MLC_QAIC_RUNNER_PATH'] = os.path.join(env['MLC_QAIC_SOFTWARE_KIT_PATH'], "build", "utils", "qaic-runner")

    if '+PATH' not in env:
        env['+PATH'] = []

    env['MLC_QAIC_COMPUTE_SDK_INSTALL_PATH'] = os.path.join(
        os.getcwd(),
        "src",
        "install",
        "qaic-compute-" +
        env['MLC_QAIC_COMPUTE_SDK_INSTALL_MODE'])

    env['QAIC_COMPUTE_INSTALL_DIR'] = env['MLC_QAIC_COMPUTE_SDK_INSTALL_PATH']

    env['+PATH'].append(os.path.join(env['MLC_QAIC_COMPUTE_SDK_INSTALL_PATH'], "exec"))

    return {'return': 0}
