from mlc import utils
import os
import hashlib
from mlc.utils import *
from automation.utils import is_true, is_false


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = (env.get('MLC_QUIET', False) == 'yes')

    if i['input'].get('force_cache'):
        extra_cache_tags = i['input'].get('extra_cache_tags', '')
        r = automation.update_deps({
            'deps': meta['prehook_deps'] + meta['posthook_deps'],
            'update_deps': {
                'download-script': {
                    'extra_cache_tags': extra_cache_tags,
                    'force_cache': True
                },
                'extract-script': {
                    'extra_cache_tags': extra_cache_tags,
                    'force_cache': True
                }
            }
        })
        if r['return'] > 0:
            return r

    if env.get('MLC_DOWNLOAD_LOCAL_FILE_PATH'):
        filepath = env['MLC_DOWNLOAD_LOCAL_FILE_PATH']

        if not os.path.exists(filepath):
            return {'return': 1,
                    'error': 'Local file {} doesn\'t exist'.format(filepath)}

        env['MLC_EXTRACT_REMOVE_EXTRACTED'] = 'no'

    if str(env.get('MLC_DAE_EXTRACT_DOWNLOADED')
           ).lower() in ["yes", "1", "true"]:
        if (env.get('MLC_EXTRACT_FINAL_ENV_NAME', '') == '') and (
                env.get('MLC_DAE_FINAL_ENV_NAME', '') != ''):
            env['MLC_EXTRACT_FINAL_ENV_NAME'] = env['MLC_DAE_FINAL_ENV_NAME']

    if is_true(env.get('MLC_DOWNLOAD_AND_EXTRACT_SKIP_DOWNLOAD', False)):
        return {'return': 0}

    return {'return': 0}


def postprocess(i):

    env = i['env']

    if env.get('MLC_DOWNLOAD_MODE') == "dry":
        return {'return': 0}

    filepath = env.get('MLC_EXTRACT_EXTRACTED_PATH', '')
    if filepath == '':
        filepath = env.get('MLC_DOWNLOAD_DOWNLOADED_PATH', '')

    if filepath == '':
        return {'return': 1,
                'error': 'No extracted path set in "MLC_EXTRACT_EXTRACTED_PATH"'}
    if not os.path.exists(filepath):
        return {'return': 1,
                'error': 'Extracted path doesn\'t exist: {}'.format(filepath)}

    if env.get('MLC_DAE_FINAL_ENV_NAME'):
        env[env['MLC_DAE_FINAL_ENV_NAME']] = filepath

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = filepath

    return {'return': 0}
