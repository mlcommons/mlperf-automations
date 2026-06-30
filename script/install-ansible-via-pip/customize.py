from mlc import utils
import os


def preprocess(i):

    env = i['env']

    package = env.get('MLC_ANSIBLE_PIP_PACKAGE', 'ansible')
    version = env.get('MLC_ANSIBLE_VERSION_TO_INSTALL', '')

    if version:
        env['MLC_ANSIBLE_PIP_INSTALL_STRING'] = f'{package}=={version}'
    else:
        env['MLC_ANSIBLE_PIP_INSTALL_STRING'] = package

    return {'return': 0}


def postprocess(i):
    env = i['env']
    import shutil

    ansible_bin = shutil.which('ansible-playbook')
    if ansible_bin:
        env['MLC_ANSIBLE_BIN_WITH_PATH'] = ansible_bin
        env['MLC_ANSIBLE_INSTALLED_PATH'] = os.path.dirname(ansible_bin)
        env['+PATH'] = [os.path.dirname(ansible_bin)]

    return {'return': 0}
