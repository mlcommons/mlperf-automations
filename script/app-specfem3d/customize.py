from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for SPECFEM3D builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_SPECFEM3D_SRC_PATH', '')
    bin_dir = os.path.join(src_path, 'bin')

    binary = os.path.join(bin_dir, 'xspecfem3D')
    if not os.path.isfile(binary):
        return {
            'return': 1, 'error': f'SPECFEM3D binary (xspecfem3D) not found in {bin_dir}'}

    env['MLC_SPECFEM3D_INSTALL_PATH'] = src_path
    env['MLC_SPECFEM3D_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]

    return {'return': 0}
