from utils import *
from mlc import utils
import os
import re
import subprocess


def _detect_version_from_path(lib_path):
    """Try to detect jemalloc version from version.txt near lib_path, then from path components."""
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
    for part in reversed(lib_path.replace('\\', '/').split('/')):
        m = re.search(r'(\d+\.\d+(?:\.\d+)*)', part)
        if m:
            return m.group(1)
    return ''


def _extract_numeric_version(version_str):
    """Extract a clean numeric version (e.g. '5.3.0') from a version string that
    may contain git metadata like 'dev-20240101-gabcdef12'."""
    if not version_str:
        return ''
    m = re.search(r'(\d+\.\d+(?:\.\d+)*)', version_str)
    if m:
        return m.group(1)
    return version_str


def _build_version_dir(version, env):
    """Build versioned directory name with optional suffix tags."""
    suffix_tags = env.get('+MLC_INSTALL_SUFFIX_TAGS', [])
    if isinstance(suffix_tags, str):
        suffix_tags = [suffix_tags] if suffix_tags else []
    if suffix_tags:
        return version + '-' + '-'.join(suffix_tags)
    return version


def _write_version_txt(install_path, version):
    """Write version.txt in the install directory."""
    try:
        os.makedirs(install_path, exist_ok=True)
        with open(os.path.join(install_path, 'version.txt'), 'w') as f:
            f.write(version + '\n')
    except Exception:
        pass


def detect_version(i):
    """Detect jemalloc version for the MLC framework version checking.

    This function is called by the framework to validate --version, --version_min,
    and --version_max constraints.
    """
    env = i['env']
    logger = i['automation'].logger
    recursion_spaces = i.get('recursion_spaces', '')

    version = ''

    # When a user-provided path is given, detect from the actual library first
    if is_true(env.get('MLC_JEMALLOC_LIB_PATH_PROVIDED', '')):
        lib_path = env.get('MLC_JEMALLOC_LIB_PATH', '')
        if lib_path:
            version = _extract_numeric_version(
                _detect_version_from_path(lib_path))

        # Validate against requested version if specified
        requested_version = env.get('MLC_VERSION', '')
        if requested_version and version and version != 'unknown':
            if version != requested_version:
                return {
                    'return': 1,
                    'error': f'Requested version {requested_version} but library '
                             f'at path has version {version}'}

        if not version:
            version = requested_version or 'unknown'

        env['MLC_JEMALLOC_VERSION'] = version
        logger.info(
            recursion_spaces +
            '    Detected version: {}'.format(version))
        return {'return': 0, 'version': version}

    # Source build case: determine version from git/env info

    # Priority 1: version already detected and set (clean numeric only)
    if env.get('MLC_JEMALLOC_VERSION', ''):
        version = _extract_numeric_version(env['MLC_JEMALLOC_VERSION'])

    # Priority 2: from git checkout tag (set by version.# variation or --version)
    if not version and env.get('MLC_GIT_CHECKOUT_TAG', ''):
        version = _extract_numeric_version(env['MLC_GIT_CHECKOUT_TAG'])

    # Priority 3: from git checkout branch
    if not version and env.get('MLC_GIT_CHECKOUT', ''):
        version = _extract_numeric_version(env['MLC_GIT_CHECKOUT'])

    # Priority 4: try to read from jemalloc_macros.h in the source tree
    if not version:
        src_path = env.get('MLC_JEMALLOC_SRC_PATH', '')
        version_header = os.path.join(
            src_path, 'include', 'jemalloc', 'jemalloc_macros.h')
        if os.path.isfile(version_header):
            try:
                content = open(version_header).read()
                m = re.search(
                    r'#define\s+JEMALLOC_VERSION\s+"([^"]+)"', content)
                if m:
                    version = _extract_numeric_version(m.group(1))
            except Exception:
                pass

    # Priority 5: from the install path's version.txt
    if not version:
        lib_path = env.get('MLC_JEMALLOC_LIB_PATH', '')
        if lib_path:
            version = _detect_version_from_path(lib_path)

    if not version:
        version = 'unknown'

    env['MLC_JEMALLOC_VERSION'] = version

    logger.info(
        recursion_spaces +
        '    Detected version: {}'.format(version))

    return {'return': 0, 'version': version}


def preprocess(i):

    env = i['env']
    state = i['state']

    if is_true(env.get('MLC_JEMALLOC_LIB_PATH_PROVIDED', '')):
        return {'return': 0}

    configure_command = f"""{os.path.join(env['MLC_JEMALLOC_SRC_PATH'], 'configure')} --enable-autogen"""
    if env.get('MLC_JEMALLOC_LG_QUANTUM', '') != '':
        configure_command += f""" --with-lg-quantum={env['MLC_JEMALLOC_LG_QUANTUM']} """
    if env.get('MLC_JEMALLOC_LG_PAGE', '') != '':
        configure_command += f""" --with-lg-page={env['MLC_JEMALLOC_LG_PAGE']} """
    if env.get('MLC_JEMALLOC_LG_HUGEPAGE', '') != '':
        configure_command += f""" --with-lg-hugepage={env['MLC_JEMALLOC_LG_HUGEPAGE']} """

    if is_true(env.get('MLC_JEMALLOC_STATS')):
        configure_command += " --enable-stats "

    if is_true(env.get('MLC_JEMALLOC_PROF')):
        configure_command += " --enable-prof "

    if env.get('MLC_JEMALLOC_CONFIG', '') != '':
        configure_command += f""" {env['MLC_JEMALLOC_CONFIG'].replace("'", "")} """

    # Determine install prefix
    if env.get('MLC_OUTDIRNAME', ''):
        version = env.get(
            'MLC_JEMALLOC_VERSION', env.get(
                'MLC_GIT_CHECKOUT', 'unknown'))
        version_dir = _build_version_dir(version, env)
        prefix = os.path.join(env['MLC_OUTDIRNAME'], version_dir)
    else:
        prefix = os.getcwd()

    configure_command += f""" --prefix {prefix}"""

    env['MLC_JEMALLOC_CONFIGURE_COMMAND'] = configure_command

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']

    os_info = i['os_info']

    # Case 1: user-provided library path (path.# variation)
    if is_true(env.get('MLC_JEMALLOC_LIB_PATH_PROVIDED', '')):
        lib_path = env.get('MLC_JEMALLOC_LIB_PATH', '')
        if not lib_path or not os.path.isdir(lib_path):
            return {
                'return': 1, 'error': 'Provided MLC_JEMALLOC_LIB_PATH does not exist: ' + str(lib_path)}
        env['MLC_JEMALLOC_LIB_PATH'] = lib_path
        env['MLC_JEMALLOC_PATH'] = os.path.dirname(lib_path)
        env['+LD_LIBRARY_PATH'] = [lib_path]
        env['MLC_DEPENDENT_CACHED_PATH'] = lib_path
        r = detect_version(i)
        if r['return'] > 0:
            return r
        return {'return': 0}

    # Case 2: source build
    if env.get('MLC_OUTDIRNAME', ''):
        version = env.get(
            'MLC_JEMALLOC_VERSION', env.get(
                'MLC_GIT_CHECKOUT', 'unknown'))
        version_dir = _build_version_dir(version, env)
        install_path = os.path.join(env['MLC_OUTDIRNAME'], version_dir)
    else:
        install_path = os.getcwd()

    lib_path = os.path.join(install_path, "lib")

    env['+LD_LIBRARY_PATH'] = [lib_path]
    env['MLC_JEMALLOC_PATH'] = install_path
    env['MLC_JEMALLOC_LIB_PATH'] = lib_path

    ext = None
    if env.get('MLC_HOST_OS_TYPE', '') == 'darwin':
        ext = ".dylib"
    elif env.get('MLC_HOST_OS_TYPE', '') == 'linux':
        ext = ".so"

    if ext:
        env['MLC_DEPENDENT_CACHED_PATH'] = os.path.join(
            lib_path, f"libjemalloc{ext}")
    else:
        env['MLC_DEPENDENT_CACHED_PATH'] = lib_path

    # Detect and set proper version
    r = detect_version(i)
    if r['return'] > 0:
        return r
    version = r['version']

    # Write version.txt
    if version and version != 'unknown':
        _write_version_txt(install_path, version)

    return {'return': 0, 'version': version}
