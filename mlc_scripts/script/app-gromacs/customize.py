from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for GROMACS builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_GROMACS_SRC_PATH', '')
    install_dir = os.path.join(src_path, 'install')
    bin_dir = os.path.join(install_dir, 'bin')

    gmx_bin = os.path.join(bin_dir, 'gmx_mpi')
    if not os.path.isfile(gmx_bin):
        return {'return': 1, 'error': f'GROMACS binary (gmx_mpi) not found in {bin_dir}'}

    env['MLC_GROMACS_BIN_PATH'] = bin_dir
    env['MLC_GROMACS_INSTALL_PATH'] = install_dir
    env['+PATH'] = [bin_dir]
    env['+LD_LIBRARY_PATH'] = [os.path.join(install_dir, 'lib')]

    return {'return': 0}
