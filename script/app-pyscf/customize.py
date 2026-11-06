from mlc import utils
import os
import glob


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for PySCF builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_PYSCF_SRC_PATH', '')
    hits = glob.glob(os.path.join(src_path, 'pyscf/lib/*.so'), recursive=True)
    if not hits:
        return {'return': 1, 'error': f'PySCF artifact not found under {src_path}'}
    bin_dir = os.path.dirname(hits[0])
    env['MLC_PYSCF_INSTALL_PATH'] = src_path
    env['MLC_PYSCF_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
