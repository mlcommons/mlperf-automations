from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    recursion_spaces = i['recursion_spaces']

    file_name_c = 'clang.exe' if os_info['platform'] == 'windows' else 'clang'

    env['FILE_NAME_C'] = file_name_c

    if 'MLC_LLVM_CLANG_BIN_WITH_PATH' not in env:

        if env.get('MLC_LLVM_DIR_PATH', '') != '':
            llvm_path = env['MLC_LLVM_DIR_PATH']
            if os.path.exists(os.path.join(llvm_path, 'bin', 'clang')):
                env['MLC_TMP_PATH'] = os.path.join(llvm_path, 'bin')
            else:
                for l in os.listdir(llvm_path):
                    if os.path.exists(os.path.join(
                            llvm_path, l, 'bin', 'clang')):
                        llvm_path = os.path.join(llvm_path, l)
                        env['MLC_LLVM_DIR_PATH'] = llvm_path
                        env['MLC_TMP_PATH'] = os.path.join(llvm_path, 'bin')

        r = i['automation'].find_artifact({'file_name': file_name_c,
                                           'env': env,
                                           'os_info': os_info,
                                           'default_path_env_key': 'PATH',
                                           'detect_version': True,
                                           'env_path_key': 'MLC_LLVM_CLANG_BIN_WITH_PATH',
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

    r = i['automation'].parse_version({'match_text': r'clang version\s*([\d.]+)',
                                       'group_number': 1,
                                       'env_key': 'MLC_LLVM_CLANG_VERSION',
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

    version = env['MLC_LLVM_CLANG_VERSION']
    env['MLC_LLVM_CLANG_CACHE_TAGS'] = 'version-' + version
    env['MLC_COMPILER_CACHE_TAGS'] = 'version-' + version + ',family-llvm'
    env['MLC_COMPILER_FAMILY'] = 'LLVM'
    env['MLC_COMPILER_VERSION'] = env['MLC_LLVM_CLANG_VERSION']

    found_file_path = env['MLC_LLVM_CLANG_BIN_WITH_PATH']

    found_path = os.path.dirname(found_file_path)

    file_name_c = os.path.basename(found_file_path)
    file_name_cpp = file_name_c.replace("clang", "clang++")

    env['MLC_LLVM_CLANG_BIN'] = file_name_c

    # General compiler for general program compilation
    env['MLC_C_COMPILER_BIN'] = file_name_c
    env['MLC_C_COMPILER_WITH_PATH'] = found_file_path
    env['MLC_C_COMPILER_FLAG_OUTPUT'] = '-o '
    env['MLC_C_COMPILER_FLAG_VERSION'] = '--version'
    env['MLC_C_COMPILER_FLAG_INCLUDE'] = '-I'

    env['MLC_CXX_COMPILER_BIN'] = file_name_cpp
    env['MLC_CXX_COMPILER_WITH_PATH'] = os.path.join(found_path, file_name_cpp)
    env['MLC_CXX_COMPILER_FLAG_OUTPUT'] = '-o '
    env['MLC_CXX_COMPILER_FLAG_VERSION'] = '--version'
    env['MLC_CXX_COMPILER_FLAG_INCLUDE'] = '-I'

    env['MLC_COMPILER_FLAGS_FAST'] = "-O4"
    # "-flto" - this flag is not always available (requires LLVMgold.so)
    env['MLC_LINKER_FLAGS_FAST'] = "-O4"
    env['MLC_COMPILER_FLAGS_DEBUG'] = "-O0"
    env['MLC_LINKER_FLAGS_DEBUG'] = "-O0"
    env['MLC_COMPILER_FLAGS_DEFAULT'] = "-O2"
    env['MLC_LINKER_FLAGS_DEFAULT'] = "-O2"

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_LLVM_CLANG_BIN_WITH_PATH']

    return {'return': 0, 'version': version}
