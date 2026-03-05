from mlc import utils
import os
import platform


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

    logger.info(
        f"{recursion_spaces}    # Requested Geekbench version: {need_version}")

    version_major = env.get(
        'MLC_GEEKBENCH_VERSION_MAJOR', need_version.split('.')[0])

    host_os_machine = env.get(
        'MLC_HOST_OS_MACHINE', platform.machine()).lower()

    # Determine platform and architecture for download URL
    if os_info['platform'] == 'windows':
        package_name = f"Geekbench-{need_version}-WindowsSetup.zip"
    elif os_info['platform'] == 'linux':
        if host_os_machine in ('aarch64', 'arm64'):
            arch_suffix = 'LinuxARMPreview'
        else:
            arch_suffix = 'Linux'
        package_name = f"Geekbench-{need_version}-{arch_suffix}.tar.gz"
    elif os_info['platform'] == 'darwin':
        package_name = f"Geekbench-{need_version}-Mac.tar.gz"
    else:
        return {'return': 1,
                'error': f"Unsupported platform: {os_info['platform']}"}

    base_url = f"https://cdn.geekbench.com/{package_name}"

    logger.info(f"{recursion_spaces}    # Prepared package URL: {base_url}")

    # Set env vars that will be picked up by the download-and-extract prehook dep
    env['MLC_GEEKBENCH_PACKAGE_URL'] = base_url
    env['MLC_GEEKBENCH_PACKAGE_NAME'] = package_name
    env['MLC_GEEKBENCH_VERSION_MAJOR'] = version_major

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger
    recursion_spaces = i.get('recursion_spaces', '')

    need_version = env.get('MLC_VERSION', '')
    version_major = env.get(
        'MLC_GEEKBENCH_VERSION_MAJOR', need_version.split('.')[0])

    # The extracted path is set by download-and-extract
    extracted_path = env.get('MLC_GEEKBENCH_EXTRACTED_PATH', '')
    if extracted_path == '':
        return {'return': 1,
                'error': 'MLC_GEEKBENCH_EXTRACTED_PATH not set - download-and-extract may have failed'}

    # Find the Geekbench directory inside the extracted path
    geekbench_dir = extracted_path
    if os.path.isdir(extracted_path):
        for d in sorted(os.listdir(extracted_path)):
            full = os.path.join(extracted_path, d)
            if os.path.isdir(full) and d.lower().startswith('geekbench'):
                geekbench_dir = full
                break

    # Determine binary name based on platform
    if os_info['platform'] == 'windows':
        bin_name = f"geekbench{version_major}.exe"
    else:
        bin_name = f"geekbench{version_major}"

    geekbench_bin = os.path.join(geekbench_dir, bin_name)

    # Make executable on Unix
    if os_info['platform'] != 'windows' and os.path.isfile(geekbench_bin):
        os.chmod(geekbench_bin, 0o755)

    env['MLC_GEEKBENCH_BIN_WITH_PATH'] = geekbench_bin
    env['MLC_GEEKBENCH_INSTALLED_PATH'] = geekbench_dir
    env['MLC_GEEKBENCH_VERSION'] = need_version
    env['MLC_GEEKBENCH_VERSION_MAJOR'] = version_major
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = geekbench_dir
    env['+PATH'] = [geekbench_dir]

    logger.info(
        f"{recursion_spaces}    # Geekbench {need_version} installed to {geekbench_dir}")

    return {'return': 0, 'version': need_version}
