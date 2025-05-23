from mlc import utils
import os
from utils import download_file, unzip_file


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    automation = i['automation']

    logger = automation.logger

    recursion_spaces = i['recursion_spaces']

    need_version = env.get('MLC_VERSION', '')
    if need_version == '':
        return {'return': 1,
                'error': 'internal problem - MLC_VERSION is not defined in env'}

    logger.info(f"{recursion_spaces}    # Requested version: {need_version}")

    version_split = need_version.split(".")
    while len(version_split) < 3:
        version_split.append("0")

    need_version = ".".join(version_split)

    host_os_bits = env['MLC_HOST_OS_BITS']

    if os_info['platform'] != 'windows':
        host_os_machine = env['MLC_HOST_OS_MACHINE']  # ABI

    # Prepare package name
    if os_info['platform'] == 'darwin':
        if host_os_bits != '64':
            return {'return': 1,
                    'error': 'this package doesn\'t support non 64-bit MacOS'}

        package_name = 'cmake-' + need_version + '-macos-universal.tar.gz'

    elif os_info['platform'] == 'windows':
        package_name = 'cmake-' + need_version + '-windows-'

        if host_os_bits == '64':
            package_name += 'x86_64'
        else:
            package_name += 'i386'

        package_name += '.zip'

    else:
        package_name = 'cmake-' + need_version + '-linux-'

        if host_os_machine.startswith(
                'arm') or host_os_machine.startswith('aarch'):
            if host_os_bits == '64':
                package_name += 'aarch64'
            else:
                return {'return': 1, 'error': 'this script doesn\'t support armv7'}
        else:
            package_name += 'x86_64'

        package_name += '.tar.gz'

    package_url = 'https://github.com/Kitware/CMake/releases/download/v' + \
        need_version + '/' + package_name

    logger.info(f"{recursion_spaces}    # Prepared package URL: {package_url}")

    logger.info('')
    logger.info(f"Downloading from {package_url} ...")

    r = download_file({
        'url': package_url})
    if r['return'] > 0:
        return r

    filename = r['filename']

    # Check what to do with this file depending on OS
    if os_info['platform'] == 'windows':
        logger.info(f"Unzipping file {filename}")

        r = unzip_file({
            'strip_folders': 1,
            'filename': filename})
        if r['return'] > 0:
            return r

        if os.path.isfile(filename):
            logger.info(f"Removing file {filename}")
            os.remove(filename)

        path_bin = os.path.join(os.getcwd(), 'bin')
        path_include = os.path.join(os.getcwd(), 'include')
    elif os_info['platform'] == 'darwin':
        path_bin = os.path.join(os.getcwd(), 'CMake.app', 'Contents', 'bin')
        path_include = os.path.join(
            os.getcwd(), 'CMake.app', 'Contents', 'include')
    else:
        path_bin = os.path.join(os.getcwd(), 'bin')
        path_include = os.path.join(os.getcwd(), 'include')

    env['MLC_CMAKE_PACKAGE'] = filename

    env['MLC_CMAKE_INSTALLED_PATH'] = path_bin
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = os.getcwd()

    bin_name = 'cmake.exe' if os_info['platform'] == 'windows' else 'cmake'

    env['MLC_CMAKE_BIN_WITH_PATH'] = os.path.join(path_bin, bin_name)

    # We don't need to check default paths here because we force install to
    # cache
    env['+PATH'] = [env['MLC_CMAKE_INSTALLED_PATH']]

    if os.path.isdir(path_include):
        env['+C_INCLUDE_PATH'] = [path_include]

    return {'return': 0}
