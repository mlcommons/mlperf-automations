from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    if is_true(env.get('CUDA_SKIP_SUDO', '')):
        env['MLC_SUDO'] = ''

    meta = i['meta']
    automation = i['automation']
    version = env.get('MLC_VERSION')

    if version not in env.get('MLC_CUDA_LINUX_FILENAME', ''):
        supported_versions = list(meta['versions'].keys())
        return {'return': 1, 'error': "Only CUDA versions {} are supported now".format(
            ', '.join(supported_versions))}

    install_prefix = env.get('MLC_CUDA_INSTALL_PREFIX', os.getcwd())

    env['MLC_CUDA_INSTALL_PREFIX'] = install_prefix

    extra_install_args = ''

    if str(env.get('MLC_CUDA_DRIVER_INSTALL_OVERRIDE', '')) != '':
        extra_install_args += ' --override-driver-check'

    recursion_spaces = i['recursion_spaces']
    nvcc_bin = "nvcc"

    env['WGET_URL'] = "https://developer.download.nvidia.com/compute/cuda/" + \
        env['MLC_VERSION'] + "/local_installers/" + \
        env['MLC_CUDA_LINUX_FILENAME']

    extra_options = env.get('CUDA_ADDITIONAL_INSTALL_OPTIONS', '')
    if is_true(env.get('MLC_CUDA_INSTALL_DRIVER', '')):
        extra_options += " --driver"
    env['CUDA_ADDITIONAL_INSTALL_OPTIONS'] = extra_options

    env['MLC_CUDA_INSTALLED_PATH'] = os.path.join(install_prefix, 'install')
    env['MLC_NVCC_BIN_WITH_PATH'] = os.path.join(
        install_prefix, 'install', 'bin', nvcc_bin)
    env['MLC_GET_DEPENDENT_CACHED_PATH'] = env['MLC_NVCC_BIN_WITH_PATH']

    env['MLC_CUDA_EXTRA_INSTALL_ARGS'] = extra_install_args

    # Set CUDA_RUN_FILE_LOCAL_PATH to empty if not set for backwards
    # compatibility in download file
    env['CUDA_RUN_FILE_LOCAL_PATH'] = env.get('CUDA_RUN_FILE_LOCAL_PATH', '')

    return {'return': 0}
