from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for LAMMPS builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_LAMMPS_SRC_PATH', '')
    install_dir = os.path.join(src_path, 'install')
    bin_dir = os.path.join(install_dir, 'bin')

    lmp_bin = os.path.join(bin_dir, 'lmp')
    if not os.path.isfile(lmp_bin):
        return {'return': 1, 'error': f'LAMMPS binary (lmp) not found in {bin_dir}'}

    env['MLC_LAMMPS_BIN_PATH'] = bin_dir
    env['MLC_LAMMPS_INSTALL_PATH'] = install_dir
    env['+PATH'] = [bin_dir]
    env['+LD_LIBRARY_PATH'] = [os.path.join(install_dir, 'lib')]

    return {'return': 0}
