from mlc import utils
import os
import shutil


def preprocess(i):

    # MLC script internal variables
    env = i['env']
    logger = i['automation'].logger
    extra_cache_tags = []
    if env.get('MLC_EXTRA_CACHE_TAGS', '').strip() == '':
        logger.info('')
        extra_cache_tags_str = input(
            'Enter extra tags for the custom CACHE entry separated by comma: ')

        extra_cache_tags = extra_cache_tags_str.strip().split(',')

    return {'return': 0, 'add_extra_cache_tags': extra_cache_tags}


def postprocess(i):

    env = i['env']

    path = env.get('MLC_CUSTOM_CACHE_ENTRY_PATH', '').strip()

    if path != '':
        if not os.path.isdir(path):
            os.makedirs(path)
    else:
        path = os.getcwd()

    x = ''
    env_key = env.get('MLC_CUSTOM_CACHE_ENTRY_ENV_KEY', '')
    if env_key != '':
        x = env_key + '_'

    env['MLC_CUSTOM_CACHE_ENTRY_{}PATH'.format(x)] = path
    env['MLC_CUSTOM_CACHE_ENTRY_PATH'] = path

    env_key2 = env.get('MLC_CUSTOM_CACHE_ENTRY_ENV_KEY2', '')
    v = env.get(env_key2, '')
    real_path = v if v != '' else path

    env['MLC_CUSTOM_CACHE_ENTRY_{}REAL_PATH'.format(x)] = real_path

    return {'return': 0}
