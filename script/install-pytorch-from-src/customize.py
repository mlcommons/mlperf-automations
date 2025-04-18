from mlc import utils
import os
from utils import is_true


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    if is_true(env.get('MLC_MLPERF_INFERENCE_INTEL_LANGUAGE_MODEL', '')):
        i['run_script_input']['script_name'] = "run-intel-mlperf-inference-v3_1"
        run_cmd = "CC=clang CXX=clang++ USE_CUDA=OFF python -m pip install -e . "

        env['MLC_RUN_CMD'] = run_cmd
    elif env.get('MLC_MLPERF_INFERENCE_INTEL_MODEL', '') in ["resnet50", "retinanet"]:
        i['run_script_input']['script_name'] = "run-intel-mlperf-inference-vision"
        run_cmd = f"CC={env['MLC_C_COMPILER_WITH_PATH']} CXX={env['MLC_CXX_COMPILER_WITH_PATH']} USE_CUDA=OFF python -m pip install -e . "

        env['MLC_RUN_CMD'] = run_cmd

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

    return {'return': 0}
