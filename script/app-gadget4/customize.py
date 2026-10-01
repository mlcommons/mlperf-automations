from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported for GADGET-4 builds'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    src_path = env.get('MLC_GADGET4_SRC_PATH', '')

    binary = os.path.join(src_path, 'Gadget4')
    if not os.path.isfile(binary):
        return {'return': 1, 'error': f'GADGET-4 binary (Gadget4) not found in {src_path}'}

    env['MLC_GADGET4_INSTALL_PATH'] = src_path
    env['MLC_GADGET4_BIN_PATH'] = src_path
    env['+PATH'] = [src_path]

    return {'return': 0}
