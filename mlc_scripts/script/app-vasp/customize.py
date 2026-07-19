from mlc import utils
import os


def preprocess(i):

    env = i['env']
    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for VASP builds'}

    vasp_src = env.get('MLC_VASP_SRC_PATH', '')
    if not vasp_src or not os.path.isdir(vasp_src):
        return {'return': 1, 'error': 'VASP requires a license. Set MLC_VASP_SRC_PATH to your VASP source directory.'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_VASP_SRC_PATH', '')
    bin_dir = os.path.join(src_path, 'bin')

    vasp_std = os.path.join(bin_dir, 'vasp_std')
    if not os.path.isfile(vasp_std):
        return {'return': 1, 'error': f'VASP binary (vasp_std) not found in {bin_dir}'}

    env['MLC_VASP_BIN_PATH'] = bin_dir
    env['MLC_VASP_INSTALL_PATH'] = src_path
    env['+PATH'] = [bin_dir]
    env['+LD_LIBRARY_PATH'] = [bin_dir]

    return {'return': 0}
