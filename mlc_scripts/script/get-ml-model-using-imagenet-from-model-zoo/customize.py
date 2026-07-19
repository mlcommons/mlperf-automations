from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    automation = i['automation']

    cm = automation.action_object

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
