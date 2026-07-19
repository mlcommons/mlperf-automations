from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    return {'return': 0}


def postprocess(i):
    env = i['env']

    env['MLC_ML_MODEL_BERT_VOCAB_FILE_WITH_PATH'] = env['MLC_DATASET_SQUAD_VOCAB_PATH']

    return {'return': 0}
