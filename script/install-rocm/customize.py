from mlc import utils
import os
import glob


def preprocess(i):
    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    # Check standard and versioned ROCm install paths
    installed_path = ""
    for candidate in ["/opt/rocm/bin"] + sorted(glob.glob("/opt/rocm-*/bin"), reverse=True):
        if os.path.isfile(os.path.join(candidate, "rocminfo")):
            installed_path = candidate
            break

    if not installed_path:
        return {'return': 1, 'error': 'ROCm installation not found after install'}

    env['MLC_ROMLC_INSTALLED_PATH'] = installed_path
    env['MLC_ROMLC_BIN_WITH_PATH'] = os.path.join(installed_path, "rocminfo")
    env['+PATH'] = [installed_path]

    return {'return': 0}
