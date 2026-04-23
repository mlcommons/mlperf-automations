from mlc import utils
import os
import glob
import re

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


def preprocess(i):
    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    # Determine install prefix:
    # 1. If explicitly set via input, use that
    # 2. If sudo is available, default to "/" (installs to /opt/rocm)
    # 3. Otherwise, use MLC cache directory (no root needed)
    install_prefix = env.get('MLC_ROCM_INSTALL_PREFIX', '').strip()
    if install_prefix == '':
        if env.get('MLC_SUDO_USER', '') == 'yes':
            install_prefix = '/'
        else:
            install_prefix = os.getcwd()

    env['MLC_ROCM_INSTALL_PREFIX'] = install_prefix

    version = env.get('MLC_VERSION', '')

    # Source build: set up git tag and cmake command, skip runfile logic
    if env.get('MLC_ROCM_BUILD_FROM_SRC', '') == 'yes':
        env['MLC_GIT_CHECKOUT_TAG'] = f'rocm-{version}'

        src_path = env.get('MLC_ROCM_LLVM_SRC_PATH', '')
        build_install_prefix = os.path.join(os.getcwd(), 'install')
        env['MLC_ROCM_INSTALL_PREFIX'] = build_install_prefix

        targets = 'AMDGPU;X86'
        projects = 'clang;lld;compiler-rt;clang-tools-extra'
        runtimes = 'libcxx;libcxxabi;openmp'

        q = "'"
        cmake_cmd = (
            f'cmake {os.path.join(src_path, "llvm")} -GNinja'
            f' -DCMAKE_BUILD_TYPE=Release'
            f' -DCMAKE_INSTALL_PREFIX={build_install_prefix}'
            f' -DLLVM_ENABLE_PROJECTS={q}{projects}{q}'
            f' -DLLVM_ENABLE_RUNTIMES={q}{runtimes}{q}'
            f' -DLLVM_TARGETS_TO_BUILD={q}{targets}{q}'
            f' -DLLVM_ENABLE_RTTI=ON'
            f' -DLLVM_INSTALL_UTILS=ON'
            f' -DLLVM_ENABLE_ASSERTIONS=OFF'
            f' -DLLVM_ENABLE_PER_TARGET_RUNTIME_DIR=OFF'
        )
        env['MLC_ROCM_CMAKE_CMD'] = cmake_cmd
        i['run_script_input']['script_name'] = 'run-src'
        return {'return': 0}

    # For ROCm 7+, resolve the runfile download URL
    major_version = int(version.split('.')[0]) if version else 0

    if major_version >= 7:
        os_flavor = env.get('MLC_HOST_OS_FLAVOR', 'ubuntu')
        os_version = env.get('MLC_HOST_OS_VERSION', '')

        if 'ubuntu' in os_flavor or 'debian' in os_flavor:
            runfile_base_url = f"https://repo.radeon.com/rocm/installer/rocm-runfile-installer/rocm-rel-{version}/ubuntu/{os_version}/"
        else:
            runfile_base_url = f"https://repo.radeon.com/rocm/installer/rocm-runfile-installer/rocm-rel-{version}/rhel/{os_version}/"

        # Fetch directory listing to find the runfile name
        try:
            response = urlopen(runfile_base_url)
            html = response.read().decode('utf-8')
            match = re.search(r'(rocm-installer[^"]+\.run)', html)
            if match:
                runfile_name = match.group(1)
                env['MLC_DOWNLOAD_URL'] = runfile_base_url + runfile_name
                env['MLC_DOWNLOAD_FILENAME'] = runfile_name
                env['MLC_ROCM_RUNFILE_NAME'] = runfile_name
                env['MLC_ROCM_USE_RUNFILE'] = 'yes'
            else:
                return {'return': 1, 'error': f'Could not find ROCm runfile installer at {runfile_base_url}'}
        except Exception as e:
            return {'return': 1, 'error': f'Failed to fetch ROCm runfile listing from {runfile_base_url}: {e}'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    # Source build: look for clang in install dir, create amdclang symlinks
    if env.get('MLC_ROCM_BUILD_FROM_SRC', '') == 'yes':
        install_dir = env.get('MLC_ROCM_INSTALL_PREFIX', os.path.join(os.getcwd(), 'install'))
        bin_dir = os.path.join(install_dir, 'bin')

        clang_path = os.path.join(bin_dir, 'clang')
        if not os.path.isfile(clang_path):
            return {'return': 1, 'error': f'ROCm LLVM build failed: clang not found at {clang_path}'}

        # Create amdclang symlinks
        symlinks = {
            'amdclang': 'clang',
            'amdclang++': 'clang++',
            'amdflang': 'flang-new',
        }
        for link_name, target in symlinks.items():
            link_path = os.path.join(bin_dir, link_name)
            target_path = os.path.join(bin_dir, target)
            if os.path.isfile(target_path) and not os.path.exists(link_path):
                os.symlink(target, link_path)
                print(f'  Created symlink: {link_name} -> {target}')

        env['MLC_ROMLC_INSTALLED_PATH'] = bin_dir
        env['MLC_ROMLC_BIN_WITH_PATH'] = os.path.join(bin_dir, 'rocminfo') if os.path.isfile(os.path.join(bin_dir, 'rocminfo')) else clang_path
        env['+PATH'] = [bin_dir]
        return {'return': 0}

    install_prefix = env.get('MLC_ROCM_INSTALL_PREFIX', '/')
    cur_dir = os.getcwd()

    # Build search paths from multiple sources
    search_prefixes = set()
    search_prefixes.add(install_prefix)
    search_prefixes.add(cur_dir)  # MLC cache dir where script ran
    search_prefixes.add('/')      # standard /opt/rocm

    search_dirs = []
    for prefix in search_prefixes:
        # Standard package installs: /opt/rocm/bin, /opt/rocm-*/bin
        prefix_opt = os.path.join(prefix, 'opt')
        if os.path.isdir(prefix_opt):
            for p in [os.path.join(prefix_opt, 'rocm', 'bin')] + sorted(glob.glob(os.path.join(prefix_opt, 'rocm-*', 'bin')), reverse=True):
                if os.path.isdir(p) and p not in search_dirs:
                    search_dirs.append(p)
        # Untar installs: <prefix>/rocm-*/bin (no opt/ subdirectory)
        for p in sorted(glob.glob(os.path.join(prefix, 'rocm-*', 'bin')), reverse=True):
            if os.path.isdir(p) and p not in search_dirs:
                search_dirs.append(p)

    print(f"  install_prefix = {install_prefix}")
    print(f"  cur_dir = {cur_dir}")
    print(f"  Searching for rocminfo in: {search_dirs}")

    installed_path = ""
    for candidate in search_dirs:
        rocminfo_path = os.path.join(candidate, "rocminfo")
        if os.path.isfile(rocminfo_path):
            installed_path = candidate
            print(f"  Found rocminfo at: {rocminfo_path}")
            break

    if not installed_path:
        # Last resort: find rocminfo anywhere under current dir
        for p in sorted(glob.glob(os.path.join(cur_dir, '**', 'rocminfo'), recursive=True)):
            if os.path.isfile(p):
                installed_path = os.path.dirname(p)
                print(f"  Found rocminfo via recursive search at: {p}")
                break

    if not installed_path:
        return {'return': 1, 'error': f'ROCm installation not found after install. Searched: {search_dirs}. Also searched recursively under {cur_dir}'}

    env['MLC_ROMLC_INSTALLED_PATH'] = installed_path
    env['MLC_ROMLC_BIN_WITH_PATH'] = os.path.join(installed_path, "rocminfo")
    env['+PATH'] = [installed_path]

    return {'return': 0}
