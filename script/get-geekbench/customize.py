from mlc import utils
import os
import platform
import glob


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
        package_name = f"Geekbench-{need_version}-Mac.zip"
    else:
        return {'return': 1,
                'error': f"Unsupported platform: {os_info['platform']}"}

    base_url = f"https://cdn.geekbench.com/{package_name}"

    logger.info(f"{recursion_spaces}    # Prepared package URL: {base_url}")

    # Set env vars that will be picked up by the download-and-extract prehook
    # dep
    env['MLC_GEEKBENCH_PACKAGE_URL'] = base_url
    env['MLC_GEEKBENCH_PACKAGE_NAME'] = package_name
    env['MLC_GEEKBENCH_VERSION_MAJOR'] = version_major

    # If a local file is provided, pass it to download-and-extract
    # so it skips downloading and uses the local file directly
    local_file = env.get('MLC_GEEKBENCH_LOCAL_FILE', '')
    if local_file:
        if not os.path.isfile(local_file):
            return {'return': 1,
                    'error': f"Local file not found: {local_file}"}
        logger.info(
            f"{recursion_spaces}    # Using local file: {local_file}")
        env['MLC_DOWNLOAD_LOCAL_FILE_PATH'] = local_file

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

    # Determine binary path based on platform
    if os_info['platform'] == 'windows':
        bin_name = f"geekbench{version_major}.exe"
        geekbench_bin = os.path.join(geekbench_dir, bin_name)

    elif os_info['platform'] == 'darwin':
        # macOS: binary is inside the .app bundle
        # e.g. Geekbench 6.app/Contents/MacOS/Geekbench 6
        app_pattern = os.path.join(extracted_path, 'Geekbench*.app')
        app_matches = glob.glob(app_pattern)
        if app_matches:
            app_dir = app_matches[0]
            macos_dir = os.path.join(app_dir, 'Contents', 'MacOS')
            # Find the binary inside MacOS dir
            geekbench_bin = None
            if os.path.isdir(macos_dir):
                for f in os.listdir(macos_dir):
                    if f.lower().startswith('geekbench'):
                        geekbench_bin = os.path.join(macos_dir, f)
                        break
            if geekbench_bin is None:
                geekbench_bin = os.path.join(
                    macos_dir, f"Geekbench {version_major}")
            geekbench_dir = macos_dir
        else:
            # Fallback: try flat binary name
            bin_name = f"geekbench{version_major}"
            geekbench_bin = os.path.join(geekbench_dir, bin_name)

    else:
        # Linux
        bin_name = f"geekbench{version_major}"
        geekbench_bin = os.path.join(geekbench_dir, bin_name)

    print(os_info)
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
    logger.info(
        f"{recursion_spaces}    # Geekbench binary: {geekbench_bin}")

    return {'return': 0, 'version': need_version}
