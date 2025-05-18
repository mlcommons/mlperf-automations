from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    env['IPEX_DIR'] = env['MLC_IPEX_SRC_REPO_PATH']

    if is_true(env.get('MLC_USE_LLVM_FOR_IPEX', '')):
        env['DNNL_GRAPH_BUILD_COMPILER_BACKEND'] = 1
        env['USE_LLVM'] = env['MLC_LLVM_INSTALLED_PATH']
        env['LLVM_DIR'] = os.path.join(
            env['MLC_LLVM_INSTALLED_PATH'], "lib", "cmake", "llvm")

    run_cmd = "python setup.py clean && python setup.py install"

    env['MLC_RUN_CMD'] = run_cmd

    return {'return': 0}


def postprocess(i):

    env = i['env']
    env['MLC_IPEX_BUILD_PATH'] = os.path.join(os.getcwd(), "ipex_src", "build")
    env['MLC_IPEX_INSTALLED_PATH'] = os.path.join(
        env['MLC_IPEX_BUILD_PATH'],
        "Release",
        "packages",
        "intel_extension_for_pytorch")
    env['MLC_DEPENDENT_CACHED_PATH'] = env['MLC_IPEX_INSTALLED_PATH']

    return {'return': 0}
