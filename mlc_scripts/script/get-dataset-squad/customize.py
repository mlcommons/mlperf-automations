from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    return {'return': 0}


def postprocess(i):
    env = i['env']

    env['MLC_DATASET_SQUAD_PATH'] = os.path.dirname(
        env['MLC_DATASET_SQUAD_VAL_PATH'])
    env['MLC_DATASET_PATH'] = os.path.dirname(
        env['MLC_DATASET_SQUAD_VAL_PATH'])
    # env['MLC_DATASET_SQUAD_VAL_PATH'] = os.path.join(os.getcwd(), env['MLC_VAL_FILENAME'])

    return {'return': 0}
