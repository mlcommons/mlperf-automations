from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    env['MLC_GIT_CHECKOUT'] = "v" + env['MLC_VERSION']
    quiet = is_true(env.get('MLC_QUIET', False))

    return {'return': 0}


def postprocess(i):

    env = i['env']
    env['+C_INCLUDE_PATH'] = []
    env['+CPLUS_INCLUDE_PATH'] = []
    env['+LD_LIBRARY_PATH'] = []

    protobuf_install_path = os.path.join(os.getcwd(), "install")
    env['MLC_GOOGLE_PROTOBUF_SRC_PATH'] = env['MLC_GIT_REPO_CHECKOUT_PATH']
    env['MLC_GOOGLE_PROTOBUF_INSTALL_PATH'] = protobuf_install_path
    env['+C_INCLUDE_PATH'].append(
        os.path.join(
            protobuf_install_path,
            "include"))
    env['+CPLUS_INCLUDE_PATH'].append(
        os.path.join(protobuf_install_path, "include"))

    if os.path.exists(os.path.join(protobuf_install_path, "lib")):
        env['+LD_LIBRARY_PATH'].append(
            os.path.join(protobuf_install_path, "lib"))
    elif os.path.exists(os.path.join(protobuf_install_path, "lib64")):
        env['+LD_LIBRARY_PATH'].append(
            os.path.join(protobuf_install_path, "lib64"))
    else:
        return {
            'return': 1, 'error': f'Protobuf library path not found in {protobuf_install_path}'}

    return {'return': 0}
