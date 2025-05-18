from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    code_path = os.path.join(
        env['MLC_GIT_REPO_CHECKOUT_PATH'],
        "closed",
        "fpgaconvnet",
        "code")
    network_env_name = env['MLC_TINY_NETWORK_NAME'].replace("-", "_").upper()
    env['MLC_TINY_FPGACONVNET_NETWORK_ENV_NAME'] = network_env_name
    env['MLC_TINY_FPGACONVNET_' + network_env_name + '_CODE_PATH'] = code_path

    board = env.get('MLC_TINY_BOARD', 'zc706')

    benchmark = env.get('MLC_TINY_BENCHMARK', 'ic')

    run_dir = os.path.join(code_path, board, benchmark)
    env['MLC_TINY_FPGACONVNET_' + network_env_name + '_RUN_DIR'] = run_dir

    run_cmd = "cd " + run_dir + " && " + \
        env['MLC_PYTHON_BIN_WITH_PATH'] + " " + "create_config.py"

    env['ML_MODEL_FILE_WITH_PATH'] = env['MLC_ML_MODEL_FILE_WITH_PATH']
    env['MLC_RUN_CMD'] = run_cmd
    env['MLC_RUN_DIR'] = run_dir

    return {'return': 0}


def postprocess(i):

    env = i['env']

    network = env['MLC_TINY_NETWORK_NAME']
    env['MLC_TINY_FPGACONVNET_NETWORK_NAME'] = network
    network_env_name = env['MLC_TINY_FPGACONVNET_NETWORK_ENV_NAME']

    json_location = os.path.join(
        env['MLC_RUN_DIR'],
        env['MLC_TINY_NETWORK_NAME'] + ".json")
    if os.path.exists(json_location):
        print(
            f"JSON configuration file for {network} created at {json_location}")
    else:
        return {'return': 1, 'error': "JSON configuration file generation failed"}

    env['MLC_TINY_FPGACONVNET_CONFIG_FILE_' +
        network_env_name + '_PATH'] = json_location
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = json_location

    return {'return': 0}
