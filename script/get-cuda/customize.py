from mlc import utils
from utils import is_true
import os
import json


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if is_true(env.get('CUDA_SKIP_SUDO', '')):
        env['MLC_SUDO'] = ''

    recursion_spaces = i['recursion_spaces']

    if os_info['platform'] == 'windows':
        file_name = env['MLC_TMP_FILE_TO_CHECK_WINDOWS']

        if env.get('MLC_INPUT', '').strip() == '' and env.get(
                'MLC_TMP_PATH', '').strip() == '':
            # Check in "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
            paths = []
            for path in ["C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA",
                         "C:\\Program Files (x86)\\NVIDIA GPU Computing Toolkit\\CUDA"]:
                if os.path.isdir(path):
                    dirs = os.listdir(path)
                    for dr in dirs:
                        path2 = os.path.join(path, dr, 'bin')
                        if os.path.isdir(path2):
                            paths.append(path2)

            if len(paths) > 0:
                tmp_paths = ';'.join(paths)
                tmp_paths += ';' + os.environ.get('PATH', '')

                env['MLC_TMP_PATH'] = tmp_paths
                env['MLC_TMP_PATH_IGNORE_NON_EXISTANT'] = 'yes'

    else:
        file_name = env['MLC_TMP_FILE_TO_CHECK_UNIX']

        # paths to cuda are not always in PATH - add a few typical locations to search for
        # (unless forced by a user)

        if env.get('MLC_INPUT', '').strip() == '' and env.get(
                'MLC_TMP_PATH', '').strip() == '':
            system_path = os.environ.get('PATH')
            if system_path:
                system_path = system_path + ":"
            env['MLC_TMP_PATH'] = system_path + \
                '/usr/local/cuda/bin:/usr/cuda/bin:/usr/local/cuda-11/bin:/usr/cuda-11/bin:/usr/local/cuda-12/bin:/usr/cuda-12/bin:/usr/local/packages/cuda'
            env['MLC_TMP_PATH_IGNORE_NON_EXISTANT'] = 'yes'

    if is_true(env['MLC_CUDA_FULL_TOOLKIT_INSTALL']):
        env_key = 'MLC_NVCC_BIN_WITH_PATH'
        path_env_key = 'PATH'
    else:
        env_key = 'MLC_CUDA_RT_WITH_PATH'
        path_env_key = 'LD_LIBRARY_PATH'
    env['MLC_TMP_ENV_KEY'] = env_key

    if env_key not in env:
        r = i['automation'].find_artifact({'file_name': file_name,
                                           'env': env,
                                           'os_info': os_info,
                                           'default_path_env_key': path_env_key,
                                           'detect_version': True,
                                           'env_path_key': env_key,
                                           'run_script_input': i['run_script_input'],
                                           'recursion_spaces': recursion_spaces})
        if r['return'] > 0:
            if os_info['platform'] == 'windows':
                return r

            if r['return'] == 16 and is_true(
                    env['MLC_CUDA_FULL_TOOLKIT_INSTALL']):
                env['MLC_REQUIRE_INSTALL'] = "yes"
                return {'return': 0}
            else:
                return r

    return {'return': 0}


def detect_version(i):
    env = i['env']
    if is_true(env['MLC_CUDA_FULL_TOOLKIT_INSTALL']):
        return detect_version_nvcc(i)
    else:
        return detect_version_cuda_lib(i)


def detect_version_nvcc(i):
    r = i['automation'].parse_version({'match_text': r'release\s*([\d.]+)',
                                       'group_number': 1,
                                       'env_key': 'MLC_CUDA_VERSION',
                                       'which_env': i['env']})
    if r['return'] > 0:
        return r

    version = r['version']

    logger = i['automation'].logger

    logger.info(i['recursion_spaces'] + '    Detected version: {}'.format(version))

    return {'return': 0, 'version': version}


def detect_version_cuda_lib(i):

    env = i['env']
    logger = i['automation'].logger
    logger.info(env)
    cuda_rt_file_path = env['MLC_CUDA_RT_WITH_PATH']
    cuda_lib_path = os.path.dirname(cuda_rt_file_path)
    cuda_path = os.path.abspath(os.path.join(cuda_lib_path, os.pardir))

    cuda_version = "version-missing"

    version_json = os.path.join(cuda_path, "version.json")
    if os.path.exists(version_json):
        with open(version_json) as f:
            version_info = json.load(f)
            cuda_version_info = version_info.get('cuda_cudart')
            if cuda_version_info:
                cuda_version = cuda_version_info.get('version')

    env['MLC_CUDA_VERSION'] = cuda_version
    version = cuda_version

    logger.info(i['recursion_spaces'] + '    Detected version: {}'.format(version))

    return {'return': 0, 'version': version}


def postprocess(i):

    os_info = i['os_info']

    env = i['env']
    logger = i['automation'].logger
    
    r = detect_version(i)
    if r['return'] > 0:
        return r
    version = r['version']

    env['MLC_CUDA_CACHE_TAGS'] = 'version-' + version

    found_file_path = env[env['MLC_TMP_ENV_KEY']]

    if is_true(env['MLC_CUDA_FULL_TOOLKIT_INSTALL']):

        cuda_path_bin = os.path.dirname(found_file_path)
        env['MLC_CUDA_PATH_BIN'] = cuda_path_bin

        cuda_path = os.path.dirname(cuda_path_bin)
        env['MLC_CUDA_INSTALLED_PATH'] = cuda_path
        env['MLC_NVCC_BIN'] = os.path.basename(found_file_path)

    else:
        # We traverse backwards until we find a path with include dir
        parent_path = os.path.dirname(found_file_path)
        env['MLC_CUDA_PATH_LIB'] = parent_path
        parent_path = os.path.dirname(parent_path)
        while os.path.isdir(parent_path):
            if os.path.exists(os.path.join(parent_path, "include")):
                logger.info("Path is " + parent_path)
                found_path = parent_path
                cuda_path = found_path
                env['MLC_CUDA_INSTALLED_PATH'] = cuda_path
                break
            else:
                parent_path = os.path.dirname(parent_path)

    if 'MLC_CUDA_INSTALLED_PATH' not in env:
        return {
            'return': 1, 'error': "No CUDA installation path with an include directory is found"}

    env['CUDA_HOME'] = cuda_path
    env['CUDA_PATH'] = cuda_path

    cuda_system_path_install = False
    system_path = os.environ.get('PATH')
    if os.path.join(cuda_path, "bin") in system_path.split(":"):
        cuda_system_path_install = True

    # Check extra paths
    for key in ['+C_INCLUDE_PATH', '+CPLUS_INCLUDE_PATH',
                '+LD_LIBRARY_PATH', '+DYLD_FALLBACK_LIBRARY_PATH']:
        env[key] = []

    # Include
    cuda_path_include = os.path.join(cuda_path, 'include')
    if os.path.isdir(cuda_path_include):
        if os_info['platform'] != 'windows' and not cuda_system_path_install:
            env['+C_INCLUDE_PATH'].append(cuda_path_include)
            env['+CPLUS_INCLUDE_PATH'].append(cuda_path_include)

        env['MLC_CUDA_PATH_INCLUDE'] = cuda_path_include

    # Lib
    if os_info['platform'] == 'windows':
        extra_dir = 'x64'
    else:
        extra_dir = ''

    for d in ['lib64', 'lib']:
        cuda_path_lib = os.path.join(cuda_path, d)

        if extra_dir != '':
            cuda_path_lib = os.path.join(cuda_path_lib, extra_dir)

        if os.path.isdir(cuda_path_lib):
            if not cuda_system_path_install:
                env['+LD_LIBRARY_PATH'].append(cuda_path_lib)
                env['+DYLD_FALLBACK_LIBRARY_PATH'].append(cuda_path_lib)

            env['MLC_CUDA_PATH_LIB'] = cuda_path_lib
            break

    if '+ LDFLAGS' not in env:
        env['+ LDFLAGS'] = []
    if 'MLC_CUDA_PATH_LIB' in env and not cuda_system_path_install:
        x = env['MLC_CUDA_PATH_LIB']
        if ' ' in x:
            x = '"' + x + '"'
        env['+ LDFLAGS'].append("-L" + x)

    env['MLC_CUDA_VERSION_STRING'] = "cu" + \
        env['MLC_CUDA_VERSION'].replace(".", "")
    env['MLC_MLPERF_SUT_NAME_RUN_CONFIG_SUFFIX5'] = env['MLC_CUDA_VERSION_STRING']

    return {'return': 0, 'version': version}
