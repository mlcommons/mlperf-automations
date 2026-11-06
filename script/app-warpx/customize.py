from mlc import utils
import os
import glob


def preprocess(i):
    if i['os_info']['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for WarpX builds'}
    return {'return': 0}


def postprocess(i):
    env = i['env']
    src_path = env.get('MLC_WARPX_SRC_PATH', '')
    compiler_tag = env.get('MLC_COMPILER_FAMILY', '') or 'default'
    libs = glob.glob(os.path.join(src_path, 'build-' + compiler_tag, 'bin/warpx*'))
    if not libs:
        return {'return': 1, 'error': f'WarpX artifact not found under {src_path}'}
    bin_dir = os.path.dirname(libs[0])
    env['MLC_WARPX_INSTALL_PATH'] = os.path.join(src_path, 'build-' + compiler_tag)
    env['MLC_WARPX_BIN_PATH'] = bin_dir
    env['+PATH'] = [bin_dir]
    return {'return': 0}
