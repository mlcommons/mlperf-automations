from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Grid builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_GRID_SRC_PATH', '')
    lib = os.path.join(src_path, 'build', 'lib', 'libGrid.a')
    if not os.path.isfile(lib):
        return {'return': 1, 'error': f'Grid library not found at {lib}'}
    bin_dir = os.path.dirname(lib)
    env['MLC_GRID_INSTALL_PATH'] = os.path.join(src_path, 'build')
    env['MLC_GRID_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
