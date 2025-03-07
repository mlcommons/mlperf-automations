from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    recursion_spaces = i['recursion_spaces']
    file_name_c = 'oneapi.exe' if os_info['platform'] == 'windows' else 'oneapi-cli'

    if 'MLC_ONEAPI_BIN_WITH_PATH' not in env:
        if env.get('MLC_ONEAPI_DIR_PATH', '') != '':
            oneapi_path = env['MLC_ONEAPI_DIR_PATH']
            if os.path.exists(os.path.join(oneapi_path, 'bin', 'oneapi-cli')):
                env['MLC_TMP_PATH'] = os.path.join(oneapi_path, 'bin')

    if 'MLC_ONEAPI_BIN_WITH_PATH' not in env:
        r = i['automation'].find_artifact({'file_name': file_name_c,
                                           'env': env,
                                           'os_info': os_info,
                                           'default_path_env_key': 'PATH',
                                           'detect_version': True,
                                           'env_path_key': 'MLC_ONEAPI_BIN_WITH_PATH',
                                           'run_script_input': i['run_script_input'],
                                           'recursion_spaces': recursion_spaces})
        if r['return'] > 0:
            # Uncomment when MLC script for installing oneapi compiler is integrated
            # Initial finding suggests that oneapi could be installed without hastle in linux using apt, but is tricky in windows

            #           if r['return'] == 16:
            #               if env.get('MLC_TMP_FAIL_IF_NOT_FOUND','').lower() == 'yes':
            #                   return r
            #
            #               print (recursion_spaces+'    # {}'.format(r['error']))
            #
            #               # Attempt to run installer
            #               r = {'return':0, 'skip':True, 'script':{'tags':'install,gcc,src'}}

            return r

    return {'return': 0}


def detect_version(i):
    r = i['automation'].parse_version({'match_text': r'^.*$',
                                       'group_number': 1,
                                       'env_key': 'MLC_ONEAPI_VERSION',
                                       'which_env': i['env']})
    if r['return'] > 0:
        if 'clang' in r['error']:
            return {'return': 0, 'version': -1}
        return r
    version = r['version']

    print(i['recursion_spaces'] + '    Detected version: {}'.format(version))

    return {'return': 0, 'version': version}


def postprocess(i):

    env = i['env']
    r = detect_version(i)
    if r['return'] > 0:
        return r

    env['MLC_COMPILER_FAMILY'] = 'ONEAPI'
    version = r['version']
    env['MLC_COMPILER_VERSION'] = env['MLC_ONEAPI_VERSION']
    env['MLC_GCC_CACHE_TAGS'] = 'version-' + version
    env['MLC_COMPILER_CACHE_TAGS'] = 'version-' + version + ',family-oneapi'

    found_file_path = env['MLC_ONEAPI_BIN_WITH_PATH']

    found_path = os.path.dirname(found_file_path)

    env['MLC_ONEAPI_INSTALLED_PATH'] = found_path

    file_name_c = os.path.basename(found_file_path)

    env['MLC_ONEAPI_BIN'] = file_name_c

    # General compiler for general program compilation
    env['MLC_ONEAPI_COMPILER_BIN'] = file_name_c
    env['MLC_ONEAPI_COMPILER_FLAG_OUTPUT'] = ''
    env['MLC_ONEAPI_COMPILER_WITH_PATH'] = found_file_path
    env['MLC_ONEAPI_COMPILER_FLAG_VERSION'] = 'version'

    # env['MLC_COMPILER_FLAGS_FAST'] = "-O3"
    # env['MLC_LINKER_FLAGS_FAST'] = "-O3"
    # env['MLC_COMPILER_FLAGS_DEBUG'] = "-O0"
    # env['MLC_LINKER_FLAGS_DEBUG'] = "-O0"
    # env['MLC_COMPILER_FLAGS_DEFAULT'] = "-O2"
    # env['MLC_LINKER_FLAGS_DEFAULT'] = "-O2"

    return {'return': 0, 'version': version}
