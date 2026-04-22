from mlc import utils
import os
import glob


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    recursion_spaces = i['recursion_spaces']

    file_name_c = 'amdclang'

    env['FILE_NAME_C'] = file_name_c

    if 'MLC_AMDCLANG_BIN_WITH_PATH' not in env:

        # Build search paths from ROCm installation
        search_paths = []

        if env.get('MLC_AMDCLANG_DIR_PATH', '') != '':
            d = env['MLC_AMDCLANG_DIR_PATH']
            if os.path.exists(os.path.join(d, 'bin', file_name_c)):
                search_paths.append(os.path.join(d, 'bin'))

        # Check ROCm llvm directories
        rocm_path = env.get('MLC_ROMLC_INSTALLED_PATH', '')
        if rocm_path:
            rocm_base = os.path.dirname(rocm_path)  # /opt/rocm
            llvm_bin = os.path.join(rocm_base, 'llvm', 'bin')
            if os.path.isdir(llvm_bin):
                search_paths.append(llvm_bin)

        # Check custom install prefix (from install-rocm cache)
        install_prefix = env.get('MLC_ROCM_INSTALL_PREFIX', '')
        if install_prefix:
            prefix_opt = os.path.join(install_prefix, 'opt')
            for p in [os.path.join(prefix_opt, 'rocm', 'llvm', 'bin')] + sorted(
                    glob.glob(os.path.join(prefix_opt, 'rocm-*', 'llvm', 'bin')), reverse=True):
                if os.path.isdir(p) and p not in search_paths:
                    search_paths.append(p)

        # Also check standard paths
        for p in ['/opt/rocm/llvm/bin'] + \
                sorted(glob.glob('/opt/rocm-*/llvm/bin'), reverse=True):
            if os.path.isdir(p) and p not in search_paths:
                search_paths.append(p)

        if search_paths:
            env['MLC_TMP_PATH'] = os.pathsep.join(search_paths)

        r = i['automation'].find_artifact({'file_name': file_name_c,
                                           'env': env,
                                           'os_info': os_info,
                                           'default_path_env_key': 'PATH',
                                           'detect_version': True,
                                           'env_path_key': 'MLC_AMDCLANG_BIN_WITH_PATH',
                                           'run_script_input': i['run_script_input'],
                                           'recursion_spaces': recursion_spaces})
        if r['return'] > 0:
            return r

    return {'return': 0}


def detect_version(i):
    env = i['env']
    logger = i['automation'].logger

    r = i['automation'].parse_version({'match_text': r'AMD clang version\s+([\d.]+)',
                                       'group_number': 1,
                                       'env_key': 'MLC_AMDCLANG_VERSION',
                                       'which_env': env})
    if r['return'] > 0:
        return r

    version = r['version']

    logger.info(
        f"{i['recursion_spaces']}    Detected version: {version}")

    return {'return': 0, 'version': version}


def postprocess(i):

    env = i['env']
    r = detect_version(i)
    if r['return'] > 0:
        return r

    version = r['version']
    env['MLC_COMPILER_FAMILY'] = 'AMDCLANG'
    env['MLC_COMPILER_VERSION'] = version
    env['MLC_AMDCLANG_CACHE_TAGS'] = 'version-' + version
    env['MLC_COMPILER_CACHE_TAGS'] = 'version-' + version + ',family-amdclang'

    found_file_path = env['MLC_AMDCLANG_BIN_WITH_PATH']
    found_path = os.path.dirname(found_file_path)

    env['MLC_AMDCLANG_BIN_PATH'] = found_path
    env['MLC_AMDCLANG_INSTALLED_PATH'] = os.path.dirname(found_path)
    env['MLC_AMDCLANG_LIB_PATH'] = os.path.join(
        env['MLC_AMDCLANG_INSTALLED_PATH'], 'lib')

    file_name_c = os.path.basename(found_file_path)
    file_name_cpp = 'amdclang++'
    file_name_fortran = 'amdflang'

    env['MLC_AMDCLANG_BIN'] = file_name_c

    # C compiler
    env['MLC_C_COMPILER_BIN'] = file_name_c
    env['MLC_C_COMPILER_WITH_PATH'] = found_file_path
    env['MLC_C_COMPILER_FLAG_OUTPUT'] = '-o '
    env['MLC_C_COMPILER_FLAG_VERSION'] = '--version'
    env['MLC_C_COMPILER_FLAG_INCLUDE'] = '-I'

    # C++ compiler
    env['MLC_CXX_COMPILER_BIN'] = file_name_cpp
    env['MLC_CXX_COMPILER_WITH_PATH'] = os.path.join(found_path, file_name_cpp)
    env['MLC_CXX_COMPILER_FLAG_OUTPUT'] = '-o '
    env['MLC_CXX_COMPILER_FLAG_VERSION'] = '--version'
    env['MLC_CXX_COMPILER_FLAG_INCLUDE'] = '-I'

    # Fortran compiler
    fortran_path = os.path.join(found_path, file_name_fortran)
    if os.path.exists(fortran_path):
        env['MLC_FORTRAN_COMPILER_BIN'] = file_name_fortran
        env['MLC_FORTRAN_COMPILER_WITH_PATH'] = fortran_path
        env['MLC_FORTRAN_COMPILER_FLAG_OUTPUT'] = '-o '
        env['MLC_FORTRAN_COMPILER_FLAG_VERSION'] = '--version'

    env['MLC_COMPILER_FLAGS_FAST'] = "-O3"
    env['MLC_LINKER_FLAGS_FAST'] = "-O3"
    env['MLC_COMPILER_FLAGS_DEBUG'] = "-O0"
    env['MLC_LINKER_FLAGS_DEBUG'] = "-O0"
    env['MLC_COMPILER_FLAGS_DEFAULT'] = "-O2"
    env['MLC_LINKER_FLAGS_DEFAULT'] = "-O2"

    env['+PATH'] = [found_path]

    return {'return': 0, 'version': version}
