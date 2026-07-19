from mlc import utils
from utils import is_true

import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    name = env.get('MLC_NAME', '')
    if name != '':
        name = name.strip().lower()

        r = automation.update_deps({'deps': meta['prehook_deps'],
                                    'update_deps': {
            'python-venv': {
                'name': name
            }
        }
        })
        if r['return'] > 0:
            return r

    return {'return': 0}
