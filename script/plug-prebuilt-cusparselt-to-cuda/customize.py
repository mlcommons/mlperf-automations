from mlc import utils
import os
from utils import is_true


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
        return {'return': 1, 'error': "Only CUSPARSELT versions {} are supported now".format(
            ', '.join(supported_versions))}

    env['MLC_CUSPARSELT_VERSION'] = version

    filename = env['MLC_CUSPARSELT_TAR_FILE_NAME_TEMPLATE']
    cusparselt_md5sum = env.get('MLC_CUSPARSELT_TAR_MD5SUM', '')

    cuda_version_split = env['MLC_CUDA_VERSION'].split('.')
    cuda_version_major = cuda_version_split[0]

    filename = filename.replace('{{CUDA_MAJOR_VERSION}}', cuda_version_major)

    env['MLC_CUSPARSELT_TAR_FILE_NAME'] = filename

    cusparselt_dir = filename[:-7]

    cusparselt_url = f'https://developer.download.nvidia.com/compute/cusparselt/redist/libcusparse_lt/linux-x86_64/{filename}'

    logger.info('')
    logger.info(f'URL to download CUSPARSELT: {cusparselt_url}')

    env['MLC_CUSPARSELT_TAR_DIR'] = cusparselt_dir
    env['MLC_CUSPARSELT_UNTAR_PATH'] = os.path.join(cur_dir, cusparselt_dir)
    env['WGET_URL'] = cusparselt_url
    env['MLC_DOWNLOAD_CHECKSUM'] = cusparselt_md5sum

    return {'return': 0}
