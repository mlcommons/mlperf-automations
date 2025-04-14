from mlc import utils
import os
from utils import is_true

def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    run_cmd = "./build.sh --config RelWithDebInfo --build_wheel --parallel --allow_running_as_root --skip_tests "

    if is_true(env.get('MLC_ONNXRUNTIME_GPU', '')):
        cuda_home = env['CUDA_HOME']
        run_cmd += f"--use_cuda --cuda_home {cuda_home} --cudnn_home {cuda_home}"

    env['MLC_RUN_DIR'] = env['MLC_ONNXRUNTIME_SRC_REPO_PATH']
    env['MLC_RUN_CMD'] = run_cmd

    return {'return': 0}
