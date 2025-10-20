from mlc import utils
import os
import shutil
from utils import *


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}
    env = i['env']

    if '+LIBRARY_PATH' not in env:
        env['+LIBRARY_PATH'] = []

    if 'MLC_TENSORRT_INSTALL_PATH' in env:
        env['+LIBRARY_PATH'].append(os.path.join(
            env['MLC_TENSORRT_INSTALL_PATH'], "lib"))

    hpcx_paths = []
    if is_true(env.get('BUILD_TRTLLM')):
        if os.path.exists("/opt/hpcx/ucx/lib"):
            hpcx_paths.append("/opt/hpcx/ucx/lib")
        if os.path.exists("/opt/hpcx/ucc/lib"):
            hpcx_paths.append("/opt/hpcx/ucc/lib")
        if os.path.exists("/opt/hpcx/ompi/lib"):
            hpcx_paths.append("/opt/hpcx/ompi/lib")

    cxxflags = [
        "-Wno-error=switch",
        "-DDALI_1_15=1",
        "-Wno-error=maybe-uninitialized"]

    if env.get('MLC_GCC_VERSION', '') != '':
        gcc_major_version = env['MLC_GCC_VERSION'].split(".")[0]
        if int(gcc_major_version) > 10:
            if env.get('MLC_MLPERF_INFERENCE_VERSION', '') != "4.1":
                cxxflags.append("-Wno-error=range-loop-construct")

    if env.get('MLC_MLPERF_DEVICE', '') == "inferentia":
        env['USE_INFERENTIA'] = "1"
        env['USE_NIGHTLY'] = "0"
        env['MLC_MAKE_BUILD_COMMAND'] = "build"

    if '+ CXXFLAGS' not in env:
        env['+ CXXFLAGS'] = []

    env['+ CXXFLAGS'] += cxxflags
    env['+LD_LIBRARY_PATH'] = hpcx_paths + env['+LD_LIBRARY_PATH']
    env['+PYTHONPATH'] = []
    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
