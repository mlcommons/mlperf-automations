from mlc import utils
import os


def preprocess(i):
    return {'return': 0}


def postprocess(i):
    env = i['env']

    src = env.get('MLC_WEBVOYAGER_SRC_PATH', '')
    if not src or not os.path.isdir(src):
        return {'return': 1,
                'error': f'WebVoyager checkout not found: {src!r}'}

    data_dir = os.path.join(src, 'data')
    env['MLC_AGENT_DATA_PATH'] = data_dir if os.path.isdir(data_dir) else src
    env['MLC_DATASET_WEBVOYAGER_PATH'] = src
    return {'return': 0}
