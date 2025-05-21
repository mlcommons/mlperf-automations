from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']
    env = i['env']

    # TBD
    cur_dir = os.getcwd()

    return {'return': 0}
