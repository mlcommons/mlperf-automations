from mlc import utils
import os
import glob
from utils import *


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    recursion_spaces = i['recursion_spaces']
    file_name_c = 'icx.exe' if os_info['platform'] == 'windows' else 'icx'

    if is_true(env.get('MLC_ONEAPI_CLEAN_INSTALL')):
        env['MLC_CLEAN_INSTALL'] = 'yes'

    if 'MLC_ICX_BIN_WITH_PATH' not in env:
        if env.get('MLC_ONEAPI_DIR_PATH', '') != '':
            oneapi_path = env['MLC_ONEAPI_DIR_PATH']
            # Reuse an existing install instead of re-downloading when a path is given.
            icx_candidates = [
                os.path.join(oneapi_path, 'bin', file_name_c),
                os.path.join(oneapi_path, 'compiler',
                             'latest', 'bin', file_name_c),
            ]
            icx_candidates += sorted(glob.glob(
                os.path.join(oneapi_path, 'compiler', '*', 'bin', file_name_c)))
            for icx_candidate in icx_candidates:
                if os.path.exists(icx_candidate):
                    env['MLC_TMP_PATH'] = os.path.dirname(icx_candidate)
                    break

    if 'MLC_ONEAPI_BIN_WITH_PATH' not in env:
        r = i['automation'].find_artifact({'file_name': file_name_c,
                                           'env': env,
                                           'os_info': os_info,
                                           'default_path_env_key': 'PATH',
                                           'detect_version': True,
                                           'env_path_key': 'MLC_ICX_BIN_WITH_PATH',
                                           'run_script_input': i['run_script_input'],
                                           'recursion_spaces': recursion_spaces})
        if r['return'] > 0:
            r = i['automation'].run_native_script(
                {'run_script_input': i['run_script_input'], 'env': env, 'script_name': 'install'})
            if r['return'] > 0:
                return r
            version_prefix = env['MLC_ONEAPI_INSTALL_VERSION_PREFIX']
            env['MLC_TMP_PATH'] = os.path.join(
                os.getcwd(), "install", version_prefix, "bin")

            r = i['automation'].find_artifact({'file_name': file_name_c,
                                               'env': env,
                                               'os_info': os_info,
                                               'default_path_env_key': 'PATH',
                                               'detect_version': True,
                                               'env_path_key': 'MLC_ICX_BIN_WITH_PATH',
                                               'run_script_input': i['run_script_input'],
                                               'recursion_spaces': recursion_spaces})
            if r['return'] > 0:
                return r

    return {'return': 0}


def detect_version(i):
    r = i['automation'].parse_version({'match_text': r'oneAPI\s+.* Compiler\s+([\d+.]+)',
                                       'group_number': 1,
                                       'env_key': 'MLC_ONEAPI_VERSION',
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

    env['MLC_COMPILER_FAMILY'] = 'ONEAPI'
    version = r['version']
    env['MLC_COMPILER_VERSION'] = env['MLC_ONEAPI_VERSION']
    env['MLC_ONEAPI_CACHE_TAGS'] = 'version-' + version
    env['MLC_COMPILER_CACHE_TAGS'] = 'version-' + version + ',family-oneapi'

    found_file_path = env['MLC_ICX_BIN_WITH_PATH']

    found_path = os.path.dirname(found_file_path)

    env['MLC_ONEAPI_INSTALLED_PATH'] = os.path.dirname(found_path)

    file_name_c = os.path.basename(found_file_path)

    env['MLC_ONEAPI_BIN'] = file_name_c

    # General compiler for general program compilation
    env['MLC_ONEAPI_COMPILER_BIN'] = file_name_c
    env['MLC_ONEAPI_COMPILER_FLAG_OUTPUT'] = ''
    env['MLC_ONEAPI_COMPILER_WITH_PATH'] = found_file_path
    env['MLC_ONEAPI_COMPILER_FLAG_VERSION'] = 'version'

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = found_file_path

    list_keys = ['+LD_LIBRARY_PATH']
    for key in list_keys:
        if not env.get(key):
            env[key] = []

    env['+LD_LIBRARY_PATH'].append(os.path.join(
        env['MLC_ONEAPI_INSTALLED_PATH'], "lib"))

    if is_true(env.get('MLC_ONEAPI_GET_LIBS')):
        r = get_oneapi_libraries(i)
        if r['return'] > 0:
            return r

    # env['MLC_COMPILER_FLAGS_FAST'] = "-O3"
    # env['MLC_LINKER_FLAGS_FAST'] = "-O3"
    # env['MLC_COMPILER_FLAGS_DEBUG'] = "-O0"
    # env['MLC_LINKER_FLAGS_DEBUG'] = "-O0"
    # env['MLC_COMPILER_FLAGS_DEFAULT'] = "-O2"
    # env['MLC_LINKER_FLAGS_DEFAULT'] = "-O2"

    return {'return': 0, 'version': version}


def get_oneapi_libraries(i):
    env = i['env']
    logger = i['automation'].logger

    # Prefer a user-provided install path so libraries are reused without re-downloading.
    search_roots = []
    provided = env.get('MLC_ONEAPI_DIR_PATH', '')
    if provided and os.path.isdir(provided):
        search_roots.append(provided)
    installed_path = env.get('MLC_ONEAPI_INSTALLED_PATH', '')
    if installed_path and os.path.isdir(installed_path):
        search_roots.append(installed_path)
    install_base = os.path.join(os.getcwd(), "install")
    if os.path.isdir(install_base):
        search_roots.append(install_base)

    for key in ['+LD_LIBRARY_PATH', '+LIBRARY_PATH']:
        if not env.get(key):
            env[key] = []

    lib_dirs = []

    # Compiler runtime libraries (SVML, Intel Math library, qkmalloc, ...) live together.
    compiler_libs = {
        'SVML': 'libsvml.so',
        'IMF': 'libimf.so',
        'IRNG': 'libirng.so',
        'INTLC': 'libintlc.so',
        'QKMALLOC': 'libqkmalloc.so',
        'IOMP5': 'libiomp5.so',
    }
    compiler_lib_dir = ''
    svml = _find_oneapi_lib(search_roots, 'libsvml.so')
    if svml:
        compiler_lib_dir = os.path.dirname(svml)

    for name, basename in compiler_libs.items():
        lib_path = _lib_in_dir(compiler_lib_dir, basename)
        if not lib_path:
            lib_path = _find_oneapi_lib(search_roots, basename)
        if lib_path:
            env['MLC_ONEAPI_' + name + '_LIB'] = lib_path
            lib_dir = os.path.dirname(lib_path)
            if lib_dir not in lib_dirs:
                lib_dirs.append(lib_dir)

    if env.get('MLC_ONEAPI_SVML_LIB'):
        env['MLC_ONEAPI_LIB_PATH'] = os.path.dirname(env['MLC_ONEAPI_SVML_LIB'])

    # oneMKL ships in a separate component directory.
    mkl = _find_oneapi_lib(search_roots, 'libmkl_rt.so')
    if mkl:
        env['MLC_ONEAPI_MKL_LIB'] = mkl
        env['MLC_ONEAPI_MKL_LIB_PATH'] = os.path.dirname(mkl)
        if os.path.dirname(mkl) not in lib_dirs:
            lib_dirs.append(os.path.dirname(mkl))

    for lib_dir in lib_dirs:
        if lib_dir not in env['+LD_LIBRARY_PATH']:
            env['+LD_LIBRARY_PATH'].append(lib_dir)
        if lib_dir not in env['+LIBRARY_PATH']:
            env['+LIBRARY_PATH'].append(lib_dir)

    if not lib_dirs:
        logger.warning(
            'OneAPI libraries requested via _libs but none were found under: '
            + ', '.join(search_roots))

    return {'return': 0}


def _find_oneapi_lib(search_roots, basename):
    for root in search_roots:
        if not root or not os.path.isdir(root):
            continue
        matches = glob.glob(os.path.join(root, '**', basename), recursive=True)
        if not matches:
            matches = glob.glob(
                os.path.join(root, '**', basename + '.*'), recursive=True)
        if matches:
            return sorted(matches)[0]
    return ''


def _lib_in_dir(lib_dir, basename):
    if not lib_dir or not os.path.isdir(lib_dir):
        return ''
    exact = os.path.join(lib_dir, basename)
    if os.path.exists(exact):
        return exact
    matches = sorted(glob.glob(os.path.join(lib_dir, basename + '.*')))
    return matches[0] if matches else ''
