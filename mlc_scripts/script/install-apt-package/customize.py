from mlc import utils
import os
import re


def preprocess(i):

    os_info = i['os_info']

    env = i['env']
    state = i['state']
    package_name = env['MLC_APT_PACKAGE_NAME']

    install_cmd = env.get('MLC_HOST_OS_PACKAGE_MANAGER_INSTALL_CMD')
    if not install_cmd:
        return {
            'return': 1, 'error': 'Package manager installation command not detected for the given OS'}

    sudo = env.get('MLC_SUDO', '')

    env['MLC_APT_INSTALL_CMD'] = sudo + ' ' + install_cmd + ' ' + package_name

    if env.get('MLC_APT_CHECK_CMD',
               '') != '' and env['MLC_APT_INSTALL_CMD'] != '':
        env['MLC_APT_INSTALL_CMD'] = f"""{env['MLC_APT_CHECK_CMD']} || {env['MLC_APT_INSTALL_CMD']}"""

    return {'return': 0}
