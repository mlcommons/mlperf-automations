from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    logger = automation.logger

    quiet = is_true(env.get('MLC_QUIET', False))

    new_dir = env.get('MLC_CREATE_PATCH_NEW', '')
    if new_dir == '':
        return {'return': 1, 'error': 'specify NEW directory using --new'}
    if not os.path.isdir(new_dir):
        return {'return': 1,
                'error': 'NEW directory doesn\'t exist {}'.format(new_dir)}

    old_dir = env.get('MLC_CREATE_PATCH_OLD', '')
    if old_dir == '':
        return {'return': 1, 'error': 'specify OLD directory using --old'}
    if not os.path.isdir(old_dir):
        return {'return': 1,
                'error': 'OLD directory doesn\'t exist {}'.format(old_dir)}

    exclude = env.get('MLC_CREATE_PATCH_EXCLUDE', '').strip()
    x_exclude = ''

    if exclude != '':
        for e in exclude.split(','):
            x_exclude += ' --exclude={}'.format(e)

    cmd = 'diff -Naur {} {} {} > patch.patch'.format(
        x_exclude, old_dir, new_dir)

    if not quiet:
        logger.info('')
        logger.info('Running command:')
        logger.info('')
        logger.info(cmd)
        logger.info('')

    os.system(cmd)

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
