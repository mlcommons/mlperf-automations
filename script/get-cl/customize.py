from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] != 'windows':
        return {'return': 0}

    env = i['env']

    recursion_spaces = i['recursion_spaces']

    automation = i['automation']

    file_name = 'cl.exe'

    # Will check env['MLC_TMP_PATH'] if comes from installation script
    ii = {'file_name': file_name,
          'env': env,
          'os_info': os_info,
          'default_path_env_key': 'PATH',
          'detect_version': True,
          'env_path_key': 'MLC_CL_BIN_WITH_PATH',
          'run_script_input': i['run_script_input'],
          'recursion_spaces': recursion_spaces}

    rr = automation.find_artifact(ii)
    if rr['return'] > 0:
        # If not found in PATH, try a longer search
        if rr['return'] != 16:
            return rr

        if env.get('MLC_INPUT', '').strip() == '' and env.get(
                'MLC_TMP_PATH', '').strip() == '':

            print(
                i['recursion_spaces'] +
                '    Starting deep search for {} - it may take some time ...'.format(file_name))

            paths = ['C:\\Program Files\\Microsoft Visual Studio',
                     'C:\\Program Files (x86)\\Microsoft Visual Studio',
                     'C:\\Program Files (x86)\\Microsoft Visual Studio 14']

            restrict_paths = ['Hostx64\\x64']

            r = automation.find_file_deep({'paths': paths,
                                           'file_name': file_name,
                                           'restrict_paths': restrict_paths})
            if r['return'] > 0:
                return r

            found_paths = r['found_paths']

            if len(found_paths) == 0:
                return rr

            tmp_paths = ';'.join(found_paths)

            env['MLC_TMP_PATH'] = tmp_paths
            env['MLC_TMP_PATH_IGNORE_NON_EXISTANT'] = 'yes'

            ii['env'] = env

            rr = automation.find_artifact(ii)
            if rr['return'] > 0:
                return rr

        else:
            return rr

    found_path = rr['found_path']

    # Check vcvarall.bat
    state = i['state']
    script_prefix = state.get('script_prefix', [])

    # Attempt to find vcvars64.bat
    bat_file_name = 'VC\\Auxiliary\\Build\\vcvars64.bat'
    r = automation.find_file_back(
        {'path': found_path, 'file_name': bat_file_name})
    if r['return'] > 0:
        return r

    found_path_bat = r['found_path']

    if found_path_bat != '':
        path_to_vcvars = os.path.join(found_path_bat, bat_file_name)

        s = os_info['run_bat'].replace(
            '${bat_file}', '"' + path_to_vcvars + '"')

        script_prefix.append(s)

        state['script_prefix'] = script_prefix

    env['MLC_CL_BIN'] = file_name
    env['MLC_CL_BIN_WITH_PATH'] = os.path.join(found_path, file_name)

    # General compiler for general program compilation
    env['MLC_C_COMPILER_BIN'] = file_name
    env['MLC_C_COMPILER_WITH_PATH'] = os.path.join(found_path, file_name)
    env['MLC_C_COMPILER_FLAG_OUTPUT'] = '/Fe:'
    env['MLC_C_COMPILER_FLAG_VERSION'] = ''

    env['MLC_CXX_COMPILER_BIN'] = env['MLC_C_COMPILER_BIN']
    env['MLC_CXX_COMPILER_WITH_PATH'] = env['MLC_C_COMPILER_WITH_PATH']
    env['MLC_CXX_COMPILER_FLAG_OUTPUT'] = '/Fe:'
    env['MLC_CXX_COMPILER_FLAG_VERSION'] = ''

    return {'return': 0}


def detect_version(i):
    r = i['automation'].parse_version({'match_text': r'Version\s*([\d.]+)',
                                       'group_number': 1,
                                       'env_key': 'MLC_CL_VERSION',
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

    env['MLC_CL_CACHE_TAGS'] = 'version-' + version
    env['MLC_COMPILER_CACHE_TAGS'] = 'version-' + version + ',family-msvc'
    env['MLC_COMPILER_FAMILY'] = 'MSVC'
    env['MLC_COMPILER_VERSION'] = env['MLC_CL_VERSION']

    return {'return': 0, 'version': version}
