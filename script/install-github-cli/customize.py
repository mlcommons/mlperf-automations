from mlc import utils
from utils import is_true
import os
import subprocess


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    # Support custom install path via MLC_GH_INSTALL_PATH
    custom_path = env.get('MLC_GH_INSTALL_PATH', '')
    if custom_path:
        install_dir = os.path.abspath(custom_path)
    else:
        install_dir = os.path.join(os.getcwd(), 'install')

    bin_dir = os.path.join(install_dir, 'bin')

    env['MLC_TMP_PATH'] = bin_dir
    env['MLC_TMP_FAIL_IF_NOT_FOUND'] = 'yes'
    env['MLC_GH_INSTALL_DIR'] = install_dir

    sudo = env.get('MLC_SUDO', '')

    # Allow user to explicitly disable sudo via MLC_SUDO=no
    if sudo == 'no':
        sudo = ''
        env['MLC_SUDO'] = ''

    if sudo:
        # Check if sudo is actually available
        try:
            subprocess.run(['sudo', '-n', 'true'], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            sudo = ''
            env['MLC_SUDO'] = ''

    if not sudo:
        env['MLC_GH_INSTALL_WITHOUT_SUDO'] = 'yes'

    return {'return': 0}
