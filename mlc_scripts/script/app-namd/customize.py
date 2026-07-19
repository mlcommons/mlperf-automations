from mlc import utils
import os
import glob


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for NAMD builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_NAMD_SRC_PATH', '')
    install_dir = os.path.join(src_path, 'install')
    bin_dir = os.path.join(install_dir, 'bin')

    # Look for namd3 or namd2 binary
    namd_bin = None
    for name in ['namd3', 'namd2']:
        candidate = os.path.join(bin_dir, name)
        if os.path.isfile(candidate):
            namd_bin = candidate
            break

    if namd_bin is None:
        # Search in build directory
        build_dir = os.path.join(src_path, 'build')
        for name in ['namd3', 'namd2']:
            candidate = os.path.join(build_dir, name)
            if os.path.isfile(candidate):
                namd_bin = candidate
                bin_dir = build_dir
                break

    if namd_bin is None:
        return {'return': 1, 'error': f'NAMD binary not found in {bin_dir} or build directory'}

    env['MLC_NAMD_BIN_PATH'] = bin_dir
    env['MLC_NAMD_INSTALL_PATH'] = install_dir
    env['+PATH'] = [bin_dir]

    return {'return': 0}
