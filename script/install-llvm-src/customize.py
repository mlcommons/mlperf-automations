from mlc import utils
from utils import is_true
import platform
import os


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    q = '"' if os_info['platform'] == 'windows' else "'"

    clang_file_name = "clang"
    extra_cmake_options = env.get('MLC_LLVM_EXTRA_CMAKE_OPTIONS', '')

    if env.get('MLC_LLVM_INSTALLED_PATH', '') != '' and os.path.exists(
            env.get('MLC_LLVM_INSTALLED_PATH')):
        install_prefix = env['MLC_LLVM_INSTALLED_PATH']
    else:
        install_prefix = os.path.join(os.getcwd(), "install")

    if os.path.exists(os.path.join(install_prefix, "bin", "clang")) and is_true(
            env.get('MLC_LLVM_USE_INSTALLED_DIR')):
        i['run_script_input']['script_name'] = "no-install"  # skip install
    else:
        if env.get('MLC_LLVM_CONDA_ENV', '') == "yes":
            install_prefix = env['MLC_CONDA_PREFIX']
            extra_cmake_options = f"-DCMAKE_SHARED_LINKER_FLAGS=-L{install_prefix} -Wl,-rpath,{install_prefix}"

        if is_true(env.get('MLC_LLVM_16_INTEL_MLPERF_INFERENCE', '')):
            env['MLC_REQUIRE_INSTALL'] = 'yes'
            i['run_script_input']['script_name'] = "install-llvm-16-intel-mlperf-inference"
            clang_file_name = "llvm-link"
            # env['USE_LLVM'] = install_prefix
            # env['LLVM_DIR'] = os.path.join(env['USE_LLVM'], "lib", "cmake", "llvm")
        else:
            if env.get('+MLC_LLVM_ENABLE_RUNTIMES', '') != '':
                enable_runtimes = ";".join(env['+MLC_LLVM_ENABLE_RUNTIMES'])
            else:
                enable_runtimes = ''

            if env.get('+MLC_LLVM_ENABLE_PROJECTS', '') != '':
                enable_projects = ";".join(env['+MLC_LLVM_ENABLE_PROJECTS'])
            else:
                enable_projects = ''

            llvm_build_type = env['MLC_LLVM_BUILD_TYPE']

            targets_to_build = env.get('MLC_LLVM_TARGETS_TO_BUILD')
            host_platform = env.get('MLC_HOST_PLATFORM_FLAVOR')
            if not targets_to_build:
                if 'arm64' in host_platform:
                    targets_to_build = 'AArch64'
                else:
                    targets_to_build = 'X86'

            cross_compile_options = env.get('MLC_LLVM_CROSS_COMPILE_FLAGS', '')
            target_triple = env.get('MLC_LLVM_TARGET_TRIPLE', '')
            compiler_rt_target_triple_string = ""

            if target_triple != '':
                target_triple_string = f""" -DLLVM_DEFAULT_TARGET_TRIPLE="{target_triple}" """
            else:
                if env.get('MLC_HOST_OS_TYPE',
                           '') == 'darwin' and 'flang' in enable_projects:
                    target_triple = get_target_triple()
                    target_triple_string = f""" -DLLVM_DEFAULT_TARGET_TRIPLE="{target_triple}" """
                    compiler_rt_target_triple_string = f""" -DCOMPILER_RT_DEFAULT_TARGET_TRIPLE="{target_triple}" """
                else:
                    target_triple_string = ""

            cmake_cmd = f"""cmake {os.path.join(env["MLC_LLVM_SRC_REPO_PATH"], "llvm")} -GNinja -DCMAKE_BUILD_TYPE={llvm_build_type} -DLLVM_ENABLE_PROJECTS={q}{enable_projects}{q} -DLLVM_ENABLE_RUNTIMES={q}{enable_runtimes}{q} -DCMAKE_INSTALL_PREFIX={q}{install_prefix}{q} -DLLVM_ENABLE_RTTI=ON  -DLLVM_INSTALL_UTILS=ON -DLLVM_TARGETS_TO_BUILD={targets_to_build} {cross_compile_options} {target_triple_string} {compiler_rt_target_triple_string} {extra_cmake_options}"""

            env['MLC_LLVM_CMAKE_CMD'] = cmake_cmd

    need_version = env.get('MLC_VERSION', '')

    # print(cmake_cmd)

    env['MLC_LLVM_INSTALLED_PATH'] = install_prefix
    env['MLC_LLVM_CLANG_BIN_WITH_PATH'] = os.path.join(
        env['MLC_LLVM_INSTALLED_PATH'], "bin", clang_file_name)

    # env['+PATH'] = []
    return {'return': 0}


def get_target_triple():
    machine = platform.machine()       # e.g. 'arm64' or 'x86_64'
    system = platform.system().lower()  # e.g. 'darwin', 'linux'
    release = platform.release()       # e.g. '24.6.0'

    if system == "darwin":
        # Darwin = macOS, append apple-darwin
        return f"{machine}-apple-darwin{release}"
    elif system == "linux":
        return f"{machine}-pc-linux-gnu"
    elif system == "windows":
        return f"{machine}-pc-windows-msvc"
    else:
        return f"{machine}-{system}-{release}"


def postprocess(i):

    env = i['env']

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_LLVM_CLANG_BIN_WITH_PATH']

    if env.get('MLC_LLVM_CONDA_ENV', '') != "yes":
        # We don't need to check default paths here because we force install to
        # cache
        env['+PATH'] = [os.path.join(env['MLC_LLVM_INSTALLED_PATH'], "bin")]

        path_include = os.path.join(env['MLC_LLVM_INSTALLED_PATH'], 'include')
        if os.path.isdir(path_include):
            env['+C_INCLUDE_PATH'] = [path_include]

    if env.get('MLC_GIT_REPO_CURRENT_HASH', '') != '':
        env['MLC_LLVM_SRC_REPO_COMMIT'] = env['MLC_GIT_REPO_CURRENT_HASH']

    return {'return': 0}
