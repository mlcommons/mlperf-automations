from mlc import utils
import os


def preprocess(i):
    env = i['env']

    # User gave a ready-to-use local file -> use it as-is (no download/convert).
    local = env.get('MLC_AGENT_DATA_PATH', '')
    if local and os.path.isfile(local):
        env['MLC_HOTPOTQA_SKIP_CONVERT'] = 'yes'
        return {'return': 0}

    out_name = env.get('MLC_HOTPOTQA_OUTPUT_FILENAME', '') or 'hotpotqa_validation.json'
    out_path = os.path.join(os.getcwd(), out_name)
    env['MLC_HOTPOTQA_JSON_PATH'] = out_path

    # The raw split is fetched by the download prehook_dep, which runs AFTER
    # preprocess. Reference it as a shell variable so run.sh expands the final
    # path once the download has populated MLC_HOTPOTQA_RAW_PATH.
    python_bin = env.get('MLC_PYTHON_BIN_WITH_PATH', 'python3')
    script = os.path.join(env['MLC_TMP_CURRENT_SCRIPT_PATH'], 'convert_hotpotqa.py')
    env['MLC_RUN_CMD'] = (f'{python_bin} "{script}" '
                          f'"$MLC_HOTPOTQA_RAW_PATH" "{out_path}"')
    return {'return': 0}


def postprocess(i):
    env = i['env']

    if env.get('MLC_HOTPOTQA_SKIP_CONVERT') == 'yes':
        path = env.get('MLC_AGENT_DATA_PATH', '')
    else:
        path = env.get('MLC_HOTPOTQA_JSON_PATH', '')
    if not path or not os.path.isfile(path):
        return {'return': 1, 'error': f'HotpotQA JSON not produced: {path!r}'}

    env['MLC_AGENT_DATA_PATH'] = path
    env['MLC_HOTPOTQA_DATA_PATH'] = path
    env['MLC_DATASET_HOTPOTQA_PATH'] = os.path.dirname(path)
    return {'return': 0}
