from mlc import utils
import os
import glob


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for OpenFOAM builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_OPENFOAM_SRC_PATH', '')

    # OpenFOAM binaries are in platforms/<arch>/bin
    platform_dirs = glob.glob(os.path.join(src_path, 'platforms', '*', 'bin'))
    if not platform_dirs:
        return {'return': 1, 'error': f'OpenFOAM platform binaries not found in {src_path}/platforms/'}

    bin_dir = platform_dirs[0]
    lib_dir = os.path.join(os.path.dirname(bin_dir), 'lib')

    env['MLC_OPENFOAM_INSTALL_PATH'] = src_path
    env['+PATH'] = [bin_dir]
    if os.path.isdir(lib_dir):
        env['+LD_LIBRARY_PATH'] = [lib_dir]

    return {'return': 0}
