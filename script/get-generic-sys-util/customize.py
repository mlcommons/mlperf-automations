from mlc import utils
import os
import re
from utils import *


def preprocess(i):

    os_info = i['os_info']

    env = i['env']
    state = i['state']
    automation = i['automation']
    logger = automation.logger
    # Use VERSION_CMD as CHECK_CMD if no CHECK_CMD is set
    if env.get('MLC_SYS_UTIL_VERSION_CMD', '') != '' and env.get(
            'MLC_SYS_UTIL_CHECK_CMD', '') == '':
        env['MLC_SYS_UTIL_CHECK_CMD'] = env['MLC_SYS_UTIL_VERSION_CMD']

    if env.get('MLC_GENERIC_SYS_UTIL_RUN_MODE', '') == "install":
        if is_true(env.get('MLC_SYS_UTIL_INSTALL_WITH_RETRY', '')):
            i['run_script_input']['script_name'] = "install-with-retry"
        else:
            i['run_script_input']['script_name'] = "install"

    if env.get('MLC_GENERIC_SYS_UTIL_RUN_MODE', '') == "detect":
        if env.get('MLC_SYS_UTIL_VERSION_CMD', '') != '' or env.get(
                'MLC_SYS_UTIL_VERSION_CMD_OVERRIDE', '') != '':
            r = automation.run_native_script(
                {'run_script_input': i['run_script_input'], 'env': env, 'script_name': 'detect'})
            if r['return'] != 0:  # detection failed, do install via prehook_deps
                logger.warning("detection failed, going for installation")
                env['MLC_GENERIC_SYS_UTIL_INSTALL_NEEDED'] = "yes"
                return {'return': 0}
            else:  # detection is successful, no need to install
                # print("detection success")
                env['MLC_SYS_UTIL_INSTALL_CMD'] = ""
                return {'return': 0}
        else:  # No detction command available, just install
            # print("No detection possible, going for installation")
            env['MLC_GENERIC_SYS_UTIL_INSTALL_NEEDED'] = "yes"
            return {'return': 0}

    # Only "install" mode reaches here
    pm = env.get('MLC_HOST_OS_PACKAGE_MANAGER')
    util = env.get('MLC_SYS_UTIL_NAME', '')
    if util == '':
        return {
            'return': 1, 'error': 'Please select a variation specifying the sys util name'}

    package = state.get(util)
    package_name = None
    if package and pm:
        package_name = package.get(pm)

    if os_info['platform'] == 'windows' and not package_name:
        logger.info('')
        logger.warning('For now skipping get-generic-sys-util on Windows ...')
        logger.info('')

        return {'return': 0}

    if not pm:
        return {'return': 1, 'error': 'Package manager not detected for the given OS'}

    if not package:
        return {'return': 1,
                'error': f'No package name specified for {util} in the meta'}

    if not package_name:
        if str(env.get('MLC_GENERIC_SYS_UTIL_IGNORE_MISSING_PACKAGE', '')
               ).lower() in ["1", "true", "yes"]:
            logger.warning(
                f"No package name specified for {pm} and util name {util}. Ignoring it...")
            env['MLC_TMP_GENERIC_SYS_UTIL_PACKAGE_INSTALL_IGNORED'] = 'yes'
            return {'return': 0}
        else:
            return {
                'return': 1, 'error': f'No package name specified for {pm} and util name {util}'}

    if util == "libffi":
        if env.get("MLC_HOST_OS_FLAVOR", "") == "ubuntu":
            if env.get("MLC_HOST_OS_VERSION", "") in [
                    "20.04", "20.10", "21.04", "21.10"]:
                package_name = "libffi7"
            else:
                package_name = "libffi8"

    # Temporary handling of dynamic state variables
    tmp_values = re.findall(r'<<<(.*?)>>>', str(package_name))
    for tmp_value in tmp_values:
        if tmp_value not in env:
            return {'return': 1,
                    'error': 'variable {} is not in env'.format(tmp_value)}
        if tmp_value in env:
            if isinstance(package_name, str):
                package_name = package_name.replace(
                    "<<<" + tmp_value + ">>>", str(env[tmp_value]))

    install_cmd = env.get('MLC_HOST_OS_PACKAGE_MANAGER_INSTALL_CMD')
    if not install_cmd:
        return {
            'return': 1, 'error': 'Package manager installation command not detected for the given OS'}

    if pm == "brew":
        sudo = ''
    else:
        sudo = env.get('MLC_SUDO', '')
    env['MLC_SYS_UTIL_INSTALL_CMD'] = sudo + \
        ' ' + install_cmd + ' ' + package_name

    env['+PATH'] = []

    if env.get('MLC_HOST_OS_FLAVOR', '') == 'rhel':
        if env['MLC_SYS_UTIL_NAME'] == "g++12":
            env['+PATH'] = ["/opt/rh/gcc-toolset-12/root/usr/bin"]

        if env['MLC_SYS_UTIL_NAME'] == "numactl" and env['MLC_HOST_OS_VERSION'] in [
                "9.1", "9.2", "9.3"]:
            env['MLC_SYS_UTIL_INSTALL_CMD'] = ''

    if env.get('MLC_SYS_UTIL_CHECK_CMD',
               '') != '' and env['MLC_SYS_UTIL_INSTALL_CMD'] != '':
        env['MLC_SYS_UTIL_INSTALL_CMD'] = f"""{env['MLC_SYS_UTIL_CHECK_CMD']} || {env['MLC_SYS_UTIL_INSTALL_CMD']}"""

    return {'return': 0}


def detect_version(i):
    env = i['env']
    version_env_key = f"MLC_{env['MLC_SYS_UTIL_NAME'].upper()}_VERSION"
    version_check_re = env.get('MLC_SYS_UTIL_VERSION_RE', '')
    group_number = env.get('MLC_TMP_VERSION_DETECT_GROUP_NUMBER', 1)
    logger = i['automation'].logger
    # Confirm that the regex pattern and file are present
    if version_check_re == '' or not os.path.exists("tmp-ver.out"):
        version = "undetected"
    else:
        r = i['automation'].parse_version({'match_text': version_check_re,
                                           'group_number': group_number,
                                           'env_key': version_env_key,
                                           'which_env': env})

        if r['return'] > 0:
            return r

        version = r['version']
        logger.info(
            i['recursion_spaces'] +
            '    Detected version: {}'.format(version))

    return {'return': 0, 'version': version}


def postprocess(i):
    env = i['env']

    version_env_key = f"MLC_{env['MLC_SYS_UTIL_NAME'].upper()}_VERSION"

    if (env.get('MLC_SYS_UTIL_VERSION_CMD', '') != '' or env.get('MLC_SYS_UTIL_VERSION_CMD_OVERRIDE', '') != '') and env.get(version_env_key, '') == '' and not is_true(
            env.get('MLC_TMP_GENERIC_SYS_UTIL_PACKAGE_INSTALL_IGNORED', '')) and not is_true(env.get('MLC_GET_GENERIC_SYS_UTIL_INSTALL_FAILED', '')):
        automation = i['automation']

        r = automation.run_native_script(
            {'run_script_input': i['run_script_input'], 'env': env, 'script_name': 'detect'})
        if r['return'] > 0 and not is_true(
                env.get('MLC_GENERIC_SYS_UTIL_IGNORE_VERSION_DETECTION_FAILURE', False)):
            return {'return': 1, 'error': 'Version detection failed after installation. Please check the provided version command or use env.MLC_GENERIC_SYS_UTIL_IGNORE_VERSION_DETECTION_FAILURE=yes to ignore the error.'}

        elif r['return'] == 0:
            r = detect_version(i)

            if r['return'] > 0:
                return r

            version = r['version']

            env[version_env_key] = version

            # Not used now
            env['MLC_GENERIC_SYS_UTIL_' + env['MLC_SYS_UTIL_NAME'].upper() +
                '_CACHE_TAGS'] = 'version-' + version

    if env.get(version_env_key, '') == '':
        env[version_env_key] = "undetected"

    return {'return': 0, 'version': env[version_env_key]}
