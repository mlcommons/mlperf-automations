from mlc import utils
import os


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

#    if 'MLC_GIT_CHECKOUT' not in env:
#        env['MLC_GIT_CHECKOUT'] = 'releases/gcc-' + need_version

    if os_info['platform'] == 'windows':
        prefix = ''
        xos = 'windows'
        platform = 'x86_64'
        ext = '.exe'
    else:
        prefix = 'installer-'
        xos = env['MLC_HOST_OS_TYPE']
        platform = env['MLC_HOST_PLATFORM_FLAVOR']
        ext = '.sh'

    filename = 'bazel-{}-{}{}-{}{}'.format(need_version,
                                           prefix,
                                           xos,
                                           platform,
                                           ext)

    url = 'https://github.com/bazelbuild/bazel/releases/download/{}/{}'.format(
        need_version, filename)

    cur_dir = os.getcwd()

    if os_info['platform'] == 'windows':
        bazel_bin = 'bazel.exe'
        path = cur_dir
    else:
        bazel_bin = 'bazel'
        path = os.path.join(cur_dir, 'install', 'bin')

    env['MLC_BAZEL_DOWNLOAD_URL'] = url
    env['MLC_BAZEL_DOWNLOAD_FILE'] = filename

    env['MLC_BAZEL_INSTALLED_PATH'] = path
    env['MLC_BAZEL_BIN_WITH_PATH'] = os.path.join(path, bazel_bin)

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = os.getcwd()

    return {'return': 0}
