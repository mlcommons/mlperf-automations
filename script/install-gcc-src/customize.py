from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    automation = i['automation']

    logger = automation.logger

    recursion_spaces = i['recursion_spaces']

    if env.get('MLC_GCC_TARGET', '') != '':
        env['MLC_GCC_TARGET_STRING'] = f""" --target={env['MLC_GCC_TARGET']} """
    else:
        env['MLC_GCC_TARGET_STRING'] = ''

    env['MLC_GCC_INSTALLED_PATH'] = os.path.join(os.getcwd(), 'install', 'bin')

    return {'return': 0}


def postprocess(i):

    env = i['env']
    if env.get('MLC_GIT_REPO_CURRENT_HASH', '') != '':
        env['MLC_GCC_SRC_REPO_COMMIT'] = env['MLC_GIT_REPO_CURRENT_HASH']

    return {'return': 0}
