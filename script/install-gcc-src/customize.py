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


    env['MLC_GCC_INSTALLED_PATH'] = os.path.join(os.getcwd(), 'install', 'bin')

    return {'return': 0}
