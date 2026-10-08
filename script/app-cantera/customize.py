from mlc import utils
import os
import glob


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Cantera builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_CANTERA_SRC_PATH', '')
    lib_dir = os.path.join(src_path, 'build', 'lib')
    libs = glob.glob(os.path.join(lib_dir, 'libcantera_shared.so*'))
    if not libs:
        return {'return': 1, 'error': f'Cantera library not found in {lib_dir}'}
    env['MLC_CANTERA_INSTALL_PATH'] = os.path.join(src_path, 'build')
    env['MLC_CANTERA_BIN_PATH'] = lib_dir
    env['+PATH'] = [lib_dir]
    return {'return': 0}
