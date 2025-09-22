from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    recursion_spaces = i['recursion_spaces']

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
