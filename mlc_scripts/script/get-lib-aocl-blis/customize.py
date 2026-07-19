from mlc import utils
from utils import is_true
import os


def _detect_version_from_path(lib_path):
    """Try to detect AOCL version from version.txt near lib_path, then from path components."""
    import re
    # Look for version.txt as sibling of lib_path or one level up
    for candidate in [os.path.join(lib_path, '..', 'version.txt'),
                      os.path.join(lib_path, 'version.txt'),
                      os.path.join(lib_path, '..', '..', 'version.txt')]:
        vfile = os.path.normpath(candidate)
        if os.path.isfile(vfile):
            try:
                content = open(vfile).read().strip().rstrip('-')
                if content:
                    return content
            except Exception:
                pass
    # Fallback: extract version pattern from path components
    for part in reversed(lib_path.replace('\\', '/').split('/')):
        m = re.search(r'(\d+\.\d+(?:\.\d+)*)', part)
        if m:
            return m.group(1)
    return ''


def _write_version_txt(install_path, version):
    """Write version.txt in the install directory."""
    try:
        os.makedirs(install_path, exist_ok=True)
        with open(os.path.join(install_path, 'version.txt'), 'w') as f:
            f.write(version + '\n')
    except Exception:
        pass


def preprocess(i):

    os_info = i['os_info']
    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    if is_true(env.get('MLC_AOCL_BINARY_DOWNLOAD', '')):
        if not is_true(env.get('MLC_AOCL_ACCEPT_EULA', '')):
            return {
                'return': 1, 'error': 'You must accept the AMD EULA to download binary packages. Use --accept_eula=yes to accept.'}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    # Case 1: user-provided library path (path.# variation)
    if is_true(env.get('MLC_AOCL_LIB_PATH_PROVIDED', '')):
        lib_path = env.get('MLC_AOCL_BLIS_LIB_PATH', '')
        if not lib_path or not os.path.isdir(lib_path):
            return {
                'return': 1, 'error': 'Provided MLC_AOCL_BLIS_LIB_PATH does not exist: ' + str(lib_path)}
        env['MLC_AOCL_BLIS_LIB_PATH'] = lib_path
        env['+LIBRARY_PATH'] = [lib_path]
        env['+LD_LIBRARY_PATH'] = [lib_path]
        env['MLC_DEPENDENT_CACHED_PATH'] = lib_path
        if not env.get('MLC_AOCL_BLIS_VERSION'):
            env['MLC_AOCL_BLIS_VERSION'] = _detect_version_from_path(
                lib_path) or 'unknown'
        return {'return': 0}

    # Case 2: binary download
    if is_true(env.get('MLC_AOCL_BINARY_DOWNLOAD', '')):
        install_path = env.get('MLC_AOCL_BLIS_BINARY_PATH', '')
        if not install_path:
            return {'return': 1, 'error': 'Binary download path not set'}
        for entry in os.listdir(install_path):
            entry_path = os.path.join(install_path, entry)
            if os.path.isdir(entry_path) and (os.path.isdir(os.path.join(
                    entry_path, 'lib')) or os.path.isdir(os.path.join(entry_path, 'lib64'))):
                install_path = entry_path
                break
        env['MLC_AOCL_BLIS_VERSION'] = env.get('MLC_AOCL_BINARY_VERSION', '')
    else:
        # Case 3: source build
        src_path = env.get(
            'MLC_AOCL_BLIS_SRC_PATH', env.get(
                'MLC_GIT_REPO_CHECKOUT_PATH', ''))
        env['MLC_AOCL_BLIS_SRC_PATH'] = src_path
        env['MLC_AOCL_BLIS_BUILD_PATH'] = os.path.join(src_path, 'build')
        if env.get('MLC_OUTDIRNAME', ''):
            version = env.get(
                'MLC_AOCL_BLIS_VERSION', env.get(
                    'MLC_GIT_CHECKOUT', 'unknown'))
            install_path = os.path.join(
                env['MLC_OUTDIRNAME'], 'aocl-blis', version)
        else:
            install_path = os.path.join(src_path, 'install')
        if not env.get('MLC_AOCL_BLIS_VERSION'):
            env['MLC_AOCL_BLIS_VERSION'] = env.get(
                'MLC_GIT_REPO_CURRENT_HASH', env.get(
                    'MLC_GIT_CHECKOUT', 'unknown'))

    env['MLC_AOCL_BLIS_INSTALL_PATH'] = install_path
    env['MLC_AOCL_BINARY_INSTALL_PATH'] = install_path

    lib_path = os.path.join(install_path, 'lib')
    if not os.path.isdir(lib_path):
        lib_path = os.path.join(install_path, 'lib64')
    env['MLC_AOCL_BLIS_LIB_PATH'] = lib_path

    env['+LD_LIBRARY_PATH'] = [lib_path]
    env['+LIBRARY_PATH'] = [lib_path]
    env['+C_INCLUDE_PATH'] = [os.path.join(install_path, 'include')]
    env['+CPLUS_INCLUDE_PATH'] = [os.path.join(install_path, 'include')]
    env['MLC_DEPENDENT_CACHED_PATH'] = lib_path

    # Write version.txt in install directory
    version = env.get('MLC_AOCL_BLIS_VERSION', '')
    if version and not is_true(env.get('MLC_AOCL_LIB_PATH_PROVIDED', '')):
        _write_version_txt(install_path, version)

    return {'return': 0}
