from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    return {'return': 0}


def postprocess(i):
    env = i['env']

    env['MLC_DATASET_ANNOTATIONS_FILE_PATH'] = os.path.join(
        env['MLC_DATASET_ANNOTATIONS_FILE_PATH'], 'openimages-mlperf.json')
    env['MLC_DATASET_ANNOTATIONS_DIR_PATH'] = os.path.dirname(
        env['MLC_DATASET_ANNOTATIONS_FILE_PATH'])
    env['MLC_DATASET_OPENIMAGES_ANNOTATIONS_FILE_PATH'] = env['MLC_DATASET_ANNOTATIONS_FILE_PATH']
    env['MLC_DATASET_OPENIMAGES_ANNOTATIONS_DIR_PATH'] = env['MLC_DATASET_ANNOTATIONS_DIR_PATH']

    return {'return': 0}
