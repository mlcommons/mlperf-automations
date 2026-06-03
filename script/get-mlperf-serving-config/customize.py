import os


def preprocess(i):
    env = i['env']

    out_dir = env.get('MLC_OUT_DIR_PATH') or env.get(
        'MLC_TMP_CURRENT_SCRIPT_PATH', os.getcwd())
    os.makedirs(out_dir, exist_ok=True)
    env['MLC_OUT_DIR_PATH'] = out_dir
    env['MLC_MLPERF_SERVING_CONFIG_JSON'] = os.path.join(
        out_dir, 'serving_config.json')

    return {'return': 0}


def postprocess(i):
    return {'return': 0}
