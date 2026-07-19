from mlc import utils
import os
import subprocess


def preprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    # Update env variables
    env['MLC_HOST_OS_TYPE'] = os_info['platform']
    env['MLC_HOST_OS_BITS'] = os_info['bits']
    env['MLC_HOST_PYTHON_BITS'] = os_info['python_bits']

    # Update state (demo)
    # state['os_info'] = os_info

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    if os_info['platform'] != 'windows':
        if os_info['platform'] == 'linux':
            sys_cmd = "ld --verbose | grep SEARCH_DIR "
            result = subprocess.check_output(
                sys_cmd, shell=True).decode("utf-8")
            result = result.replace("SEARCH_DIR(\"=", "")
            result = result.replace("SEARCH_DIR(\"", "")
            result = result.replace("\")", "")
            result = result.replace(" ", "")
            result = result.replace("\n", "")
            dirs = result.split(';')
            lib_dir = []
            for _dir in dirs:
                if _dir != '' and _dir not in lib_dir:
                    lib_dir.append(_dir)
            env['+MLC_HOST_OS_DEFAULT_LIBRARY_PATH'] = lib_dir

        r = utils.load_txt(file_name='tmp-run.out',
                           check_if_exists=True,
                           split=True)
        if r['return'] > 0:
            return r

        s = r['list']

        state['os_uname_machine'] = s[0]
        state['os_uname_all'] = s[1]

        env['MLC_HOST_OS_MACHINE'] = state['os_uname_machine']

    else:
        env['MLC_HOST_OS_PACKAGE_MANAGER'] = "choco"

    import platform

    env['MLC_HOST_SYSTEM_NAME'] = platform.node()

    if 'MLC_HOST_OS_PACKAGE_MANAGER' not in env:
        if env.get('MLC_HOST_OS_FLAVOR', '') == "ubuntu" or \
           "debian" in env.get('MLC_HOST_OS_FLAVOR_LIKE', '') or \
           env.get('MLC_HOST_OS_FLAVOR', '') == "debian":
            env['MLC_HOST_OS_PACKAGE_MANAGER'] = "apt"
        if env.get('MLC_HOST_OS_FLAVOR', '') == "rhel" or \
                "rhel" in env.get('MLC_HOST_OS_FLAVOR_LIKE', ''):
            env['MLC_HOST_OS_PACKAGE_MANAGER'] = "dnf"
        if env.get('MLC_HOST_OS_FLAVOR', '') == "amzn":
            env['MLC_HOST_OS_PACKAGE_MANAGER'] = "yum"
        if env.get('MLC_HOST_OS_FLAVOR_LIKE', '') == "arch":
            env['MLC_HOST_OS_PACKAGE_MANAGER'] = "arch"
        if env.get('MLC_HOST_OS_FLAVOR', '') == "macos":
            env['MLC_HOST_OS_PACKAGE_MANAGER'] = "brew"
        if env.get('MLC_HOST_OS_FLAVOR', '') == "sles":
            env['MLC_HOST_OS_PACKAGE_MANAGER'] = "zypper"
    if env.get('MLC_HOST_OS_PACKAGE_MANAGER', '') == "apt":
        env['MLC_HOST_OS_PACKAGE_MANAGER_INSTALL_CMD'] = "DEBIAN_FRONTEND=noninteractive apt-get install -y"
        env['MLC_HOST_OS_PACKAGE_MANAGER_UPDATE_CMD'] = "apt-get update -y"
    elif env.get('MLC_HOST_OS_PACKAGE_MANAGER', '') == "dnf":
        env['MLC_HOST_OS_PACKAGE_MANAGER_INSTALL_CMD'] = "dnf install -y"
        env['MLC_HOST_OS_PACKAGE_MANAGER_UPDATE_CMD'] = "dnf update -y"
    elif env.get('MLC_HOST_OS_PACKAGE_MANAGER', '') == "pacman":
        env['MLC_HOST_OS_PACKAGE_MANAGER_INSTALL_CMD'] = "pacman -Sy --noconfirm"
        env['MLC_HOST_OS_PACKAGE_MANAGER_UPDATE_CMD'] = "pacman -Syu"
    elif env.get('MLC_HOST_OS_PACKAGE_MANAGER', '') == "brew":
        env['MLC_HOST_OS_PACKAGE_MANAGER_INSTALL_CMD'] = "brew install"
        env['MLC_HOST_OS_PACKAGE_MANAGER_UPDATE_CMD'] = "brew update"
    elif env.get('MLC_HOST_OS_PACKAGE_MANAGER', '') == "yum":
        env['MLC_HOST_OS_PACKAGE_MANAGER_INSTALL_CMD'] = "yum install -y --skip-broken"
        env['MLC_HOST_OS_PACKAGE_MANAGER_UPDATE_CMD'] = "yum update -y"
    elif env.get('MLC_HOST_OS_PACKAGE_MANAGER', '') == "zypper":
        env['MLC_HOST_OS_PACKAGE_MANAGER_INSTALL_CMD'] = "zypper install -y"
        env['MLC_HOST_OS_PACKAGE_MANAGER_UPDATE_CMD'] = "zypper update -y"
    elif env.get('MLC_HOST_OS_PACKAGE_MANAGER', '') == "choco":
        env['MLC_HOST_OS_PACKAGE_MANAGER_INSTALL_CMD'] = "choco install -y"
        env['MLC_HOST_OS_PACKAGE_MANAGER_UPDATE_CMD'] = "choco upgrade -y"

    if os.path.exists("/.dockerenv"):
        env['MLC_RUN_INSIDE_DOCKER'] = "yes"

    return {'return': 0}
