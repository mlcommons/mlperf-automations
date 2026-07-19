from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    if not env.get('MLC_TORRENT_DOWNLOADED_FILE_NAME'):
        return {'return': 1, 'error': 'MLC_TORRENT_DOWNLOADED_FILE_NAME is not set'}

    return {'return': 0}


def postprocess(i):

    env = i['env']
    torrent_downloaded_path = os.path.join(
        env['MLC_TORRENT_DOWNLOADED_DIR'],
        env['MLC_TORRENT_DOWNLOADED_NAME'])
    env['MLC_TORRENT_DOWNLOADED_PATH'] = torrent_downloaded_path

    if 'MLC_TORRENT_DOWNLOADED_PATH_ENV_KEY' in env:
        key = env['MLC_TORRENT_DOWNLOADED_PATH_ENV_KEY']
        env[key] = torrent_downloaded_path

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = torrent_downloaded_path

    return {'return': 0}
