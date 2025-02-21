from mlc import utils
import os


def predeps(i):
    os_info = i['os_info']

    env = i['env']
    if env.get('MLC_AOCC_TAR_FILE_PATH', '') != '':
        env['MLC_AOCC_NEEDS_TAR'] = 'yes'

    return {'return': 0}


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    exe_c = 'clang.exe' if os_info['platform'] == 'windows' else 'clang'

    if env.get('MLC_AOCC_DIR_PATH', '') != '' and env.get(
            'MLC_AOCC_BIN_WITH_PATH', '') == '':
        for f in os.listdir(env['MLC_AOCC_DIR_PATH']):
            if os.path.exists(os.path.join(
                    env['MLC_AOCC_DIR_PATH'], f, "bin", exe_c)):
                env['MLC_AOCC_BIN_WITH_PATH'] = os.path.join(
                    env['MLC_AOCC_DIR_PATH'], f, "bin", exe_c)

    if env.get('MLC_HOST_OS_FLAVOR', '') == 'rhel':
        if "12" in env.get('MLC_VERSION', '') or "12" in env.get(
                'MLC_VERSION_MIN', ''):
            if env.get('MLC_TMP_PATH', '') == '':
                env['MLC_TMP_PATH'] = ''
            env['MLC_TMP_PATH'] += "/opt/rh/aocc/root/usr/bin"
            env['MLC_TMP_PATH_IGNORE_NON_EXISTANT'] = 'yes'

    if 'MLC_AOCC_BIN_WITH_PATH' not in env:
        r = i['automation'].find_artifact({'file_name': exe_c,
                                           'env': env,
                                           'os_info': os_info,
                                           'default_path_env_key': 'PATH',
                                           'detect_version': True,
                                           'env_path_key': 'MLC_AOCC_BIN_WITH_PATH',
                                           'run_script_input': i['run_script_input'],
                                           'recursion_spaces': i['recursion_spaces']})
        if r['return'] > 0:

            return r

    return {'return': 0}


def detect_version(i):
    r = i['automation'].parse_version({'match_text': r'AMD\s+clang\sversion\s([\d.]+)',
                                       'group_number': 1,
                                       'env_key': 'MLC_AOCC_VERSION',
                                       'which_env': i['env']})
    if r['return'] > 0:
        return r
    version = r['version']

    print(i['recursion_spaces'] + '    Detected version: {}'.format(version))

    return {'return': 0, 'version': version}


def postprocess(i):

    env = i['env']
    r = detect_version(i)
    if r['return'] > 0:
        return r

    env['MLC_COMPILER_FAMILY'] = 'AOCC'
    version = r['version']
    env['MLC_COMPILER_VERSION'] = env['MLC_AOCC_VERSION']
    env['MLC_AOCC_CACHE_TAGS'] = 'version-' + version
    env['MLC_COMPILER_CACHE_TAGS'] = 'version-' + version + ',family-aocc'

    found_file_path = env['MLC_AOCC_BIN_WITH_PATH']

    found_path = os.path.dirname(found_file_path)

    env['MLC_AOCC_INSTALLED_PATH'] = found_path

    file_name_c = os.path.basename(found_file_path)
    file_name_cpp = file_name_c.replace('clang', 'clang++')
    env['FILE_NAME_CPP'] = file_name_cpp

    env['MLC_AOCC_BIN'] = file_name_c

    # General compiler for general program compilation
    env['MLC_C_COMPILER_BIN'] = file_name_c
    env['MLC_C_COMPILER_FLAG_OUTPUT'] = '-o '
    env['MLC_C_COMPILER_WITH_PATH'] = found_file_path
    env['MLC_C_COMPILER_FLAG_VERSION'] = '--version'

    env['MLC_CXX_COMPILER_BIN'] = file_name_cpp
    env['MLC_CXX_COMPILER_WITH_PATH'] = os.path.join(found_path, file_name_cpp)
    env['MLC_CXX_COMPILER_FLAG_OUTPUT'] = '-o '
    env['MLC_CXX_COMPILER_FLAG_VERSION'] = '--version'

    env['MLC_COMPILER_FLAGS_FAST'] = "-O3"
    env['MLC_LINKER_FLAGS_FAST'] = "-O3"
    env['MLC_COMPILER_FLAGS_DEBUG'] = "-O0"
    env['MLC_LINKER_FLAGS_DEBUG'] = "-O0"
    env['MLC_COMPILER_FLAGS_DEFAULT'] = "-O2"
    env['MLC_LINKER_FLAGS_DEFAULT'] = "-O2"

    return {'return': 0, 'version': version}
