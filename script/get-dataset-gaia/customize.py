from mlc import utils
import os


def preprocess(i):
    env = i['env']

    local = env.get('MLC_AGENT_DATA_PATH', '')
    if local and os.path.isfile(local):
        env['MLC_GAIA_SKIP_FETCH'] = 'yes'
        return {'return': 0}

    out_name = env.get('MLC_GAIA_OUTPUT_FILENAME', '') or 'gaia_validation.jsonl'
    out_path = os.path.join(os.getcwd(), out_name)
    env['MLC_GAIA_JSONL_PATH'] = out_path

    python_bin = env.get('MLC_PYTHON_BIN_WITH_PATH', 'python3')
    script = os.path.join(env['MLC_TMP_CURRENT_SCRIPT_PATH'], 'fetch_gaia.py')
    config = env.get('MLC_GAIA_CONFIG', '2023_all')
    split = env.get('MLC_GAIA_SPLIT', 'validation')
    env['MLC_RUN_CMD'] = (f'{python_bin} "{script}" "{out_path}" '
                          f'"{config}" "{split}"')
    return {'return': 0}


def postprocess(i):
    env = i['env']

    if env.get('MLC_GAIA_SKIP_FETCH') == 'yes':
        path = env.get('MLC_AGENT_DATA_PATH', '')
    else:
        path = env.get('MLC_GAIA_JSONL_PATH', '')
    if not path or not os.path.isfile(path):
        return {'return': 1, 'error': f'GAIA jsonl not produced: {path!r}'}

    env['MLC_AGENT_DATA_PATH'] = path
    env['MLC_GAIA_DATA_PATH'] = path
    env['MLC_DATASET_GAIA_PATH'] = os.path.dirname(path)
    return {'return': 0}
