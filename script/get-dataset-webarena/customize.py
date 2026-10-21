from mlc import utils
import os


def preprocess(i):
    return {'return': 0}


def postprocess(i):
    env = i['env']

    src = env.get('MLC_WEBARENA_SRC_PATH', '')
    if not src or not os.path.isdir(src):
        return {'return': 1,
                'error': f'WebArena checkout not found: {src!r}'}

    cfg_dir = os.path.join(src, 'config_files')
    env['MLC_AGENT_DATA_PATH'] = cfg_dir if os.path.isdir(cfg_dir) else src
    env['MLC_DATASET_WEBARENA_PATH'] = src
    return {'return': 0}
