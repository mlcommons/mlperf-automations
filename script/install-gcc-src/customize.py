from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    automation = i['automation']

    recursion_spaces = i['recursion_spaces']

    need_version = env.get('MLC_VERSION', '')
    if need_version == '':
        return {'return': 1,
                'error': 'internal problem - MLC_VERSION is not defined in env'}

    print(recursion_spaces + '    # Requested version: {}'.format(need_version))

    if 'MLC_GIT_CHECKOUT' not in env:
        env['MLC_GIT_CHECKOUT'] = 'releases/gcc-' + need_version

    env['MLC_GCC_INSTALLED_PATH'] = os.path.join(os.getcwd(), 'install', 'bin')

    return {'return': 0}
