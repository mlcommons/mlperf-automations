from mlc import utils
import os
import glob


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    recursion_spaces = i['recursion_spaces']

    # Source build: search for clang instead of rocminfo
    if env.get('MLC_ROCM_BUILD_FROM_SRC', '') == 'yes':
        file_name = 'clang'
    else:
        file_name = 'rocminfo.exe' if os_info['platform'] == 'windows' else 'rocminfo'
    env['FILE_NAME'] = file_name

    # Build search paths: check /opt paths first, then custom install prefix
    rocm_paths = []

    # Standard paths (always check these first)
    # Use os.path.exists to handle symlinks properly
    for p in ["/opt/rocm/bin"] + sorted(glob.glob("/opt/rocm-*/bin"), reverse=True):
        if os.path.exists(p) and p not in rocm_paths:
            rocm_paths.append(p)

    # Check custom install prefix (from install-rocm cache)
    install_prefix = env.get('MLC_ROCM_INSTALL_PREFIX', '')
    if install_prefix and install_prefix != '/':
        prefix_opt = os.path.join(install_prefix, 'opt')
        for p in [os.path.join(prefix_opt, 'rocm', 'bin')] + sorted(glob.glob(os.path.join(prefix_opt, 'rocm-*', 'bin')), reverse=True):
            if os.path.exists(p) and p not in rocm_paths:
                rocm_paths.append(p)
        # Source build: also check <prefix>/bin directly
        prefix_bin = os.path.join(install_prefix, 'bin')
        if os.path.exists(prefix_bin) and prefix_bin not in rocm_paths:
            rocm_paths.append(prefix_bin)

    if rocm_paths:
        env['MLC_TMP_PATH'] = os.pathsep.join(rocm_paths)
    else:
        # No ROCm found, skip search and trigger install
        env['MLC_REQUIRE_INSTALL'] = "yes"
        return {'return': 0}

    if 'MLC_ROMLC_BIN_WITH_PATH' not in env:
        r = i['automation'].find_artifact({'file_name': file_name,
                                           'env': env,
                                           'os_info': os_info,
                                           'default_path_env_key': 'PATH',
                                           'detect_version': True,
                                           'env_path_key': 'MLC_ROMLC_BIN_WITH_PATH',
                                           'run_script_input': i['run_script_input'],
                                           'recursion_spaces': recursion_spaces})
        if r['return'] > 0:
            if r['return'] == 16:
                env['MLC_REQUIRE_INSTALL'] = "yes"
                return {'return': 0}
            else:
                return r

    return {'return': 0}


def detect_version(i):
    r = i['automation'].parse_version({'match_text': r'([\d.]+[-\d+]*)',
                                       'group_number': 1,
                                       'env_key': 'MLC_ROMLC_VERSION',
                                       'which_env': i['env']})
    if r['return'] > 0:
        return r

    version = r['version']

    logger = i['automation'].logger
    logger.info(
        i['recursion_spaces'] +
        '    Detected version: {}'.format(version))
    return {'return': 0, 'version': version}


def postprocess(i):
    env = i['env']

    r = detect_version(i)

    if r['return'] > 0:
        return r

    version = r['version']
    found_file_path = env['MLC_ROMLC_BIN_WITH_PATH']

    found_path = os.path.dirname(found_file_path)
    env['MLC_ROMLC_INSTALLED_PATH'] = found_path

    env['MLC_ROMLC_CACHE_TAGS'] = 'version-' + version

    return {'return': 0, 'version': version}
