from mlc import utils
import os
import glob


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for BOUT++ builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_BOUT_SRC_PATH', '')
    libs = glob.glob(os.path.join(src_path, 'build/lib/libbout++.so*'))
    if not libs:
        return {'return': 1, 'error': f'BOUT++ artifact not found under {src_path}'}
    bin_dir = os.path.dirname(libs[0])
    env['MLC_BOUT_INSTALL_PATH'] = os.path.join(src_path, 'build')
    env['MLC_BOUT_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
