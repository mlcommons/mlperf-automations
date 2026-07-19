from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for ROMS builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_ROMS_SRC_PATH', '')
    build_dir = os.path.join(src_path, 'build')

    # Find the romsM binary
    roms_bin = os.path.join(build_dir, 'romsM')
    if not os.path.isfile(roms_bin):
        # Try install directory
        install_bin = os.path.join(src_path, 'install', 'bin')
        roms_bin = os.path.join(install_bin, 'romsM')
        if not os.path.isfile(roms_bin):
            return {'return': 1, 'error': f'ROMS binary (romsM) not found in {build_dir} or {install_bin}'}

    bin_dir = os.path.dirname(roms_bin)
    env['MLC_ROMS_BIN_PATH'] = bin_dir
    env['MLC_ROMS_INSTALL_PATH'] = src_path
    env['+PATH'] = [bin_dir]

    return {'return': 0}
