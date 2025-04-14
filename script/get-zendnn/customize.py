from mlc import utils
import os
from utils import is_true

def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    env['ZENDNN_BLIS_PATH'] = env['MLC_BLIS_INSTALL_PATH']
    env['ZENDNN_LIBM_PATH'] = env['MLC_AOCL_BUILD_PATH']

    env['ZENDNN_SRC_PATH'] = env['MLC_GIT_REPO_CHECKOUT_PATH']

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
