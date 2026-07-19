from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for NWChem builds'}

    env = i['env']

    if '+LD_LIBRARY_PATH' not in env:
        env['+LD_LIBRARY_PATH'] = []
    if '+PATH' not in env:
        env['+PATH'] = []

    # Add AOCL library paths to LD_LIBRARY_PATH
    for lp in ['MLC_AOCL_BLIS_LIB_PATH', 'MLC_AOCL_LIBFLAME_LIB_PATH', 'MLC_AOCL_SCALAPACK_LIB_PATH']:
        p = env.get(lp, '')
        if p and os.path.isdir(p):
            env['+LD_LIBRARY_PATH'].append(p)

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_NWCHEM_SRC_PATH', '')
    bin_path = os.path.join(src_path, 'bin', 'LINUX64')
    nwchem_bin = os.path.join(bin_path, 'nwchem')

    if not os.path.isfile(nwchem_bin):
        return {'return': 1, 'error': f'NWChem binary not found at {nwchem_bin}'}

    env['MLC_NWCHEM_BIN_PATH'] = bin_path
    env['MLC_NWCHEM_INSTALL_PATH'] = src_path
    env['+PATH'] = [bin_path]

    # Set up .nwchemrc data paths
    data_path = os.path.join(src_path, 'src', 'basis', 'libraries')
    nwpw_path = os.path.join(src_path, 'src', 'nwpw', 'libraryps')
    data_dir = os.path.join(src_path, 'src', 'data')

    nwchemrc = os.path.join(os.path.expanduser('~'), '.nwchemrc')
    if not os.path.exists(nwchemrc):
        with open(nwchemrc, 'w') as f:
            f.write(f'nwchem_basis_library {data_path}/\n')
            f.write(f'nwchem_nwpw_library {nwpw_path}/\n')
            f.write(f'ffield amber\n')
            f.write(f'amber_1 {data_dir}/amber_s/\n')
            f.write(f'amber_2 {data_dir}/amber_q/\n')
            f.write(f'amber_3 {data_dir}/amber_x/\n')
            f.write(f'amber_4 {data_dir}/amber_u/\n')
            f.write(f'spce {data_dir}/solvents/spce.rst\n')
            f.write(f'charmm_s {data_dir}/charmm_s/\n')
            f.write(f'charmm_x {data_dir}/charmm_x/\n')

    return {'return': 0}
