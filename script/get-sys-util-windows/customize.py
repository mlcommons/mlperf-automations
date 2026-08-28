from mlc import utils
import os
from utils import *


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    state = i['state']
    automation = i['automation']
    logger = automation.logger

    if os_info['platform'] != 'windows':
        logger.warning('get-sys-util-windows only runs on Windows. Use get-generic-sys-util for Linux/Mac.')
        return {'return': 0}

    # Use VERSION_CMD as CHECK_CMD if no CHECK_CMD is set
    if env.get('MLC_SYS_UTIL_VERSION_CMD', '') != '' and env.get('MLC_SYS_UTIL_CHECK_CMD', '') == '':
        env['MLC_SYS_UTIL_CHECK_CMD'] = env['MLC_SYS_UTIL_VERSION_CMD']

    if env.get('MLC_GENERIC_SYS_UTIL_RUN_MODE', '') == 'detect':
        if env.get('MLC_SYS_UTIL_VERSION_CMD', '') != '':
            r = automation.run_native_script(
                {'run_script_input': i['run_script_input'], 'env': env, 'script_name': 'detect'})
            if r['return'] != 0:
                logger.warning('detection failed, going for installation')
                env['MLC_GENERIC_SYS_UTIL_INSTALL_NEEDED'] = 'yes'
                return {'return': 0}
            else:
                env['MLC_SYS_UTIL_INSTALL_CMD'] = ''
                return {'return': 0}
        else:
            env['MLC_GENERIC_SYS_UTIL_INSTALL_NEEDED'] = 'yes'
            return {'return': 0}

    # Only "install" mode reaches here
    util = env.get('MLC_SYS_UTIL_NAME', '')
    if util == '':
        return {'return': 1, 'error': 'Please select a variation specifying the sys util name'}

    package = state.get(util)
    package_name = None
    if package:
        package_name = package.get('choco')

    if not package:
        return {'return': 1, 'error': f'No package entry for {util} in the meta'}

    if not package_name:
        if str(env.get('MLC_GENERIC_SYS_UTIL_IGNORE_MISSING_PACKAGE', '')).lower() in ['1', 'true', 'yes']:
            logger.warning(f'No choco package name specified for {util}. Ignoring...')
            env['MLC_TMP_GENERIC_SYS_UTIL_PACKAGE_INSTALL_IGNORED'] = 'yes'
            return {'return': 0}
        else:
            return {'return': 1, 'error': f'No choco package name specified for {util}'}

    env['MLC_SYS_UTIL_CHOCO_PACKAGE'] = package_name
    env['+PATH'] = []

    return {'return': 0}


def detect_version(i):
    env = i['env']
    version_env_key = f"MLC_{env['MLC_SYS_UTIL_NAME'].upper()}_VERSION"
    version_check_re = env.get('MLC_SYS_UTIL_VERSION_RE', '')
    group_number = env.get('MLC_TMP_VERSION_DETECT_GROUP_NUMBER', 1)
    logger = i['automation'].logger

    if version_check_re == '' or not os.path.exists('tmp-ver.out'):
        version = 'undetected'
    else:
        r = i['automation'].parse_version({'match_text': version_check_re,
                                           'group_number': group_number,
                                           'env_key': version_env_key,
                                           'which_env': env})
        if r['return'] > 0:
            return r
        version = r['version']
        logger.info(i['recursion_spaces'] + '    Detected version: {}'.format(version))

    return {'return': 0, 'version': version}


def postprocess(i):
    env = i['env']
    version_env_key = f"MLC_{env['MLC_SYS_UTIL_NAME'].upper()}_VERSION"

    if (env.get('MLC_SYS_UTIL_VERSION_CMD', '') != '') and env.get(version_env_key, '') == '' and not is_true(
            env.get('MLC_TMP_GENERIC_SYS_UTIL_PACKAGE_INSTALL_IGNORED', '')) and not is_true(
            env.get('MLC_GET_GENERIC_SYS_UTIL_INSTALL_FAILED', '')):
        automation = i['automation']

        r = automation.run_native_script(
            {'run_script_input': i['run_script_input'], 'env': env, 'script_name': 'detect'})
        if r['return'] > 0 and not is_true(
                env.get('MLC_GENERIC_SYS_UTIL_IGNORE_VERSION_DETECTION_FAILURE', False)):
            return {'return': 1, 'error': 'Version detection failed after installation. Use MLC_GENERIC_SYS_UTIL_IGNORE_VERSION_DETECTION_FAILURE=yes to ignore.'}
        elif r['return'] == 0:
            r = detect_version(i)
            if r['return'] > 0:
                return r
            version = r['version']
            env[version_env_key] = version
            env['MLC_GENERIC_SYS_UTIL_' + env['MLC_SYS_UTIL_NAME'].upper() + '_CACHE_TAGS'] = 'version-' + version

    if env.get(version_env_key, '') == '':
        env[version_env_key] = 'undetected'

    return {'return': 0, 'version': env[version_env_key]}
