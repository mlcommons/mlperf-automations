from mlc import utils
import os
from utils import is_true


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    if env.get('MLC_MMDET_TASK', '') == "automotive":
        env['MLC_MMDET_TARGET_DIR'] = env['MLC_GIT_CHECKOUT_PATH']
        pip_version = env.get('MLC_PIP_VERSION', '').strip().split('.')
        if pip_version and len(pip_version) > 1 and int(pip_version[0]) >= 23:
            env['MLC_PYTHON_PIP_COMMON_EXTRA'] = " --break-system-packages"
        run_cmd = f"{env['MLC_PYTHON_BIN_WITH_PATH']} -m pip install -r requirements/optional.txt && TORCH_CUDA_ARCH_LIST='7.0;7.5;6.1;8.0;8.6' MMCV_WITH_OPS={env['MMCV_WITH_OPS']} {env['MLC_PYTHON_BIN_WITH_PATH']} -m pip install -e . {env.get('MLC_PYTHON_PIP_COMMON_EXTRA', '')}"

    automation = i['automation']

    recursion_spaces = i['recursion_spaces']

    # assigning CUDA HOME with empty string so that mmcv would take it from
    # pytorch inbuilt CUDA bundle
    env['CUDA_HOME'] = ""
    env['MLC_RUN_CMD'] = run_cmd

    return {'return': 0}
