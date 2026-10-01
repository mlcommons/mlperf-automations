from mlc import utils
import os


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for OpenMC builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_OPENMC_SRC_PATH', '')
    binary = os.path.join(src_path, 'build', 'bin', 'openmc')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'OpenMC binary not found at {binary}'}
    bin_dir = os.path.dirname(binary)
    env['MLC_OPENMC_INSTALL_PATH'] = os.path.join(src_path, 'build')
    env['MLC_OPENMC_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
