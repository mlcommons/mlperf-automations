from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for MFEM builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_MFEM_SRC_PATH', '')
    lib = os.path.join(src_path, 'libmfem.a')
    if not os.path.isfile(lib):
        return {'return': 1, 'error': f'MFEM library not found at {lib}'}
    env['MLC_MFEM_INSTALL_PATH'] = src_path
    env['MLC_MFEM_BIN_PATH'] = os.path.join(src_path, 'examples')
    env['+PATH'] = [os.path.join(src_path, 'examples')]
    return {'return': 0}
