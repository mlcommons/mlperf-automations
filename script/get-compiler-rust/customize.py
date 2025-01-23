from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = (env.get('MLC_QUIET', False) == 'yes')

    return {'return': 0}


def postprocess(i):

    env = i['env']

    rust_path = os.path.join(os.path.expanduser('~'), ".cargo", "bin")
    env['+PATH'] = [rust_path]

    return {'return': 0}
