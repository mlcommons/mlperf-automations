from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'Windows is not supported in this script yet'}

    env = i['env']

    automation = i['automation']

    recursion_spaces = i['recursion_spaces']

    return {'return': 0}


def postprocess(i):

    env = i['env']

    env['MLC_OPENCV_BUILD_PATH'] = os.path.join(os.getcwd(), "opencv", "build")
    env['MLC_DEPENDENT_CACHED_PATH'] = env['MLC_OPENCV_BUILD_PATH']

    return {'return': 0}
