from mlc import utils
import os
import glob


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for Geant4 builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_GEANT4_SRC_PATH', '')
    hits = glob.glob(
        os.path.join(
            src_path,
            'build',
            'BuildProducts',
            'lib',
            'libG4global*'))
    if not hits:
        return {'return': 1, 'error': f'Geant4 library not found under {src_path}'}
    bin_dir = os.path.dirname(hits[0])
    env['MLC_GEANT4_INSTALL_PATH'] = os.path.join(src_path, 'build')
    env['MLC_GEANT4_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
