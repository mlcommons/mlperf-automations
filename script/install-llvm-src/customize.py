from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    q = '"' if os_info['platform'] == 'windows' else "'"

    clang_file_name = "clang"
    extra_cmake_options = ''

    install_prefix = os.path.join(os.getcwd(), "install")

    if env.get('MLC_LLVM_CONDA_ENV', '') == "yes":
        install_prefix = env['MLC_CONDA_PREFIX']
        extra_cmake_options = f"-DCMAKE_SHARED_LINKER_FLAGS=-L{install_prefix} -Wl,-rpath,{install_prefix}"

    if env.get('MLC_LLVM_16_INTEL_MLPERF_INFERENCE', '') == "yes":
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

        targets_to_buuild = env.get('MLC_LLVM_TARGETS_TO_BUILD', 'X86')

        cmake_cmd = f"""cmake {os.path.join(env["MLC_LLVM_SRC_REPO_PATH"], "llvm")} -GNinja -DCMAKE_BUILD_TYPE={llvm_build_type } -DLLVM_ENABLE_PROJECTS={q}{enable_projects}{q} -DLLVM_ENABLE_RUNTIMES={q}{enable_runtimes}{q} -DCMAKE_INSTALL_PREFIX={q}{install_prefix} -DLLVM_ENABLE_RTTI=ON  -DLLVM_INSTALL_UTILS=ON -DLLVM_TARGETS_TO_BUILD={targets_to_build} {extra_cmake_options}"""

        env['MLC_LLVM_CMAKE_CMD'] = cmake_cmd

    need_version = env.get('MLC_VERSION', '')

    # print(cmake_cmd)

    env['MLC_LLVM_INSTALLED_PATH'] = install_prefix
    env['MLC_LLVM_CLANG_BIN_WITH_PATH'] = os.path.join(
        env['MLC_LLVM_INSTALLED_PATH'], "bin", clang_file_name)

    # env['+PATH'] = []
    return {'return': 0}


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

    return {'return': 0}
