from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    script_path = i['artifact'].path

    automation = i['automation']
    logger = automation.logger
    cm = automation.action_object

    path = os.getcwd()

    url = env['MLC_IPOL_SRC_URL']

    year = env.get('MLC_IPOL_YEAR', '')
    number = env.get('MLC_IPOL_NUMBER', '')

    url = url.replace(
        '{{MLC_IPOL_YEAR}}',
        year).replace(
        '{{MLC_IPOL_NUMBER}}',
        number)

    logger.info('Downloading from {}'.format(url))

    r = cm.access({'action': 'download_file',
                   'automation': 'utils,dc2743f8450541e3',
                   'url': url})
    if r['return'] > 0:
        return r

    filename = r['filename']

    logger.info('Unzipping file {}'.format(filename))

    r = cm.access({'action': 'unzip_file',
                   'automation': 'utils,dc2743f8450541e3',
                   'filename': filename})
    if r['return'] > 0:
        return r

    if os.path.isfile(filename):
        logger.info('Removing file {}'.format(filename))
        os.remove(filename)

    # Get sub-directory from filename
    ff = os.path.splitext(filename)

    subdir = ff[0]

    env['MLC_IPOL_PATH'] = os.path.join(path, subdir)

    # Applying patch
    cmd = 'patch -p0 < {}'.format(os.path.join(script_path,
                                  'patch', '20240127.patch'))

    logger.info('Patching code: {}'.format(cmd))
    os.system(cmd)

    return {'return': 0}
