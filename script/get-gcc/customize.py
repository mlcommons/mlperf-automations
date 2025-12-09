from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    recursion_spaces = i['recursion_spaces']
    file_name_c = 'gcc.exe' if os_info['platform'] == 'windows' else 'gcc'

    if 'MLC_GCC_BIN_WITH_PATH' not in env:
        if env.get('MLC_GCC_DIR_PATH', '') != '':
            gcc_path = env['MLC_GCC_DIR_PATH']
            if os.path.exists(os.path.join(gcc_path, 'bin', 'gcc')):
                env['MLC_TMP_PATH'] = os.path.join(gcc_path, 'bin')

    if env.get('MLC_HOST_OS_FLAVOR', '') == 'rhel':
        if "12" in env.get('MLC_VERSION', '') or "12" in env.get(
                'MLC_VERSION_MIN', ''):
            if env.get('MLC_TMP_PATH', '') == '':
                env['MLC_TMP_PATH'] = ''
            env['MLC_TMP_PATH'] += "/opt/rh/gcc-toolset-12/root/usr/bin"
            env['MLC_TMP_PATH_IGNORE_NON_EXISTANT'] = 'yes'

    if 'MLC_GCC_BIN_WITH_PATH' not in env:
        r = i['automation'].find_artifact({'file_name': file_name_c,
                                           'env': env,
                                           'os_info': os_info,
                                           'default_path_env_key': 'PATH',
                                           'detect_version': True,
                                           'env_path_key': 'MLC_GCC_BIN_WITH_PATH',
                                           'run_script_input': i['run_script_input'],
                                           'recursion_spaces': recursion_spaces})
        if r['return'] > 0:
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
    r = i['automation'].parse_version({'match_text': r'\s+([\d.]+(?:\s+\d{8})?)',
                                       'group_number': 1,
                                       'env_key': 'MLC_GCC_VERSION',
                                       'which_env': i['env']})
    if r['return'] > 0:
        if 'clang' in r['error']:
            return {'return': 0, 'version': -1}
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

    env['MLC_COMPILER_FAMILY'] = 'GCC'
    version = r['version']
    env['MLC_COMPILER_VERSION'] = env['MLC_GCC_VERSION']
    env['MLC_GCC_CACHE_TAGS'] = 'version-' + version
    env['MLC_COMPILER_CACHE_TAGS'] = 'version-' + version + ',family-gcc'

    found_file_path = env['MLC_GCC_BIN_WITH_PATH']

    # found_path = os.path.dirname(os.path.realpath(found_file_path)) //Need
    # to use this if we don't want to cache specific to softlinks
    found_path = os.path.dirname(os.path.abspath(found_file_path))

    env['MLC_GCC_INSTALLED_PATH'] = os.path.dirname(
        found_path)  # /usr in case of /usr/bin/gcc

    file_name_c = os.path.basename(found_file_path)
    # G: changed next line to handle cases like gcc-8
    file_name_cpp = file_name_c.replace('gcc', 'g++')
    env['FILE_NAME_CPP'] = file_name_cpp

    env['MLC_GCC_BIN'] = file_name_c

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
