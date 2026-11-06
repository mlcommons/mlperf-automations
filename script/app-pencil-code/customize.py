from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Pencil Code builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_PENCIL_SRC_PATH', '')
    binary = os.path.join(src_path, 'samples', 'conv-slab', 'src', 'run.x')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'Pencil Code binary not found at {binary}'}
    bin_dir = os.path.dirname(binary)
    env['MLC_PENCIL_INSTALL_PATH'] = src_path
    env['MLC_PENCIL_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
