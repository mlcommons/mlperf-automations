from mlc import utils
from utils import is_true
import os


def preprocess(i):

    recursion_spaces = i['recursion_spaces']

    cur_dir = os.getcwd()

    os_info = i['os_info']

    env = i['env']

    if is_true(env.get('CUDA_SKIP_SUDO', '')):
        env['MLC_SUDO'] = ''

    meta = i['meta']
    automation = i['automation']
    logger = automation.logger

    version = env.get('MLC_VERSION')

    supported_versions = list(meta['versions'].keys())

    if version not in supported_versions:
        return {'return': 1, 'error': "Only cuDNN versions {} are supported now".format(
            ', '.join(supported_versions))}

    env['MLC_CUDNN_VERSION'] = version

    filename = env['MLC_CUDNN_TAR_FILE_NAME_TEMPLATE']
    cudnn_md5sum = env.get('MLC_CUDNN_TAR_MD5SUM', '')

    cuda_version_split = env['MLC_CUDA_VERSION'].split('.')
    cuda_version_major = cuda_version_split[0]

    filename = filename.replace('{{CUDA_MAJOR_VERSION}}', cuda_version_major)

    env['MLC_CUDNN_TAR_FILE_NAME'] = filename

    cudnn_dir = filename[:-7]

    cudnn_url = f'https://developer.download.nvidia.com/compute/cudnn/redist/cudnn/linux-x86_64/{filename}'

    logger.info('')
    logger.info(f'URL to download cuDNN: {cudnn_url}')

    env['MLC_CUDNN_TAR_DIR'] = cudnn_dir
    env['MLC_CUDNN_UNTAR_PATH'] = os.path.join(cur_dir, cudnn_dir)
    env['WGET_URL'] = cudnn_url
    env['MLC_DOWNLOAD_CHECKSUM'] = cudnn_md5sum

    return {'return': 0}
