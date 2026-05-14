from utils import *
from mlc import utils
import os
import subprocess


def _detect_version_from_path(lib_path):
    """Try to detect jemalloc version from version.txt near lib_path, then from path components."""
    import re
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
        version = env.get('MLC_JEMALLOC_VERSION', env.get('MLC_GIT_CHECKOUT', 'unknown'))
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
            return {'return': 1, 'error': 'Provided MLC_JEMALLOC_LIB_PATH does not exist: ' + str(lib_path)}
        env['MLC_JEMALLOC_LIB_PATH'] = lib_path
        env['MLC_JEMALLOC_PATH'] = os.path.dirname(lib_path)
        env['+LD_LIBRARY_PATH'] = [lib_path]
        env['MLC_DEPENDENT_CACHED_PATH'] = lib_path
        if not env.get('MLC_JEMALLOC_VERSION'):
            env['MLC_JEMALLOC_VERSION'] = _detect_version_from_path(lib_path) or 'unknown'
        return {'return': 0}

    # Case 2: source build
    if env.get('MLC_OUTDIRNAME', ''):
        version = env.get('MLC_JEMALLOC_VERSION', env.get('MLC_GIT_CHECKOUT', 'unknown'))
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

    # Write version.txt
    version = env.get('MLC_JEMALLOC_VERSION', '')
    if version:
        _write_version_txt(install_path, version)

    return {'return': 0}
