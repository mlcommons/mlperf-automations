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

    # For ROCm 7+, resolve the runfile download URL
    version = env.get('MLC_VERSION', '')
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

    install_prefix = env.get('MLC_ROCM_INSTALL_PREFIX', '/')

    # Check install prefix paths first, then standard /opt paths
    search_dirs = []

    # Custom prefix: ROCm installs to <prefix>/opt/rocm-<version>
    prefix_opt = os.path.join(install_prefix, 'opt')
    if os.path.isdir(prefix_opt):
        for p in [os.path.join(prefix_opt, 'rocm', 'bin')] + sorted(glob.glob(os.path.join(prefix_opt, 'rocm-*', 'bin')), reverse=True):
            if os.path.isdir(p):
                search_dirs.append(p)

    # Standard paths as fallback
    for p in ["/opt/rocm/bin"] + sorted(glob.glob("/opt/rocm-*/bin"), reverse=True):
        if os.path.isdir(p) and p not in search_dirs:
            search_dirs.append(p)

    installed_path = ""
    for candidate in search_dirs:
        if os.path.isfile(os.path.join(candidate, "rocminfo")):
            installed_path = candidate
            break

    if not installed_path:
        return {'return': 1, 'error': 'ROCm installation not found after install'}

    env['MLC_ROMLC_INSTALLED_PATH'] = installed_path
    env['MLC_ROMLC_BIN_WITH_PATH'] = os.path.join(installed_path, "rocminfo")
    env['+PATH'] = [installed_path]

    return {'return': 0}
