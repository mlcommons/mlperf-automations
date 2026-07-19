from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    env['TPP_PEX_DIR'] = env['MLC_TPP_PEX_SRC_REPO_PATH']
    env['DNNL_GRAPH_BUILD_COMPILER_BACKEND'] = 1
    env['USE_LLVM'] = env['MLC_LLVM_INSTALLED_PATH']
    env['LLVM_DIR'] = os.path.join(
        env['MLC_LLVM_INSTALLED_PATH'], "lib", "cmake", "llvm")

    run_cmd = "python setup.py clean && python setup.py install"

    env['MLC_RUN_DIR'] = env['TPP_PEX_DIR']
    env['MLC_RUN_CMD'] = run_cmd

    return {'return': 0}
