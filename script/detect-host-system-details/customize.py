from mlc import utils
import os


def preprocess(i):

    env = i['env']

    platform_details_path = env.get('MLC_PLATFORM_DETAILS_FILE_PATH', '')
    if not platform_details_path:
        return {'return': 1, 'error': 'MLC_PLATFORM_DETAILS_FILE_PATH is not set. '
                'Ensure get,platform-details runs before detect,host,system,details.'}

    CMD = (
        f"{env['MLC_PYTHON_BIN_WITH_PATH']} "
        f"{env['MLC_TMP_CURRENT_SCRIPT_PATH']}/detect.py "
        f"--input {platform_details_path}"
    )
    env['MLC_RUN_CMD'] = CMD

    return {'return': 0}


def postprocess(i):

    env = i['env']

    r = utils.load_txt(file_name='tmp-run.out',
                       check_if_exists=True,
                       split=True)
    if r['return'] > 0:
        return r

    for line in r['list']:
        j = line.find(':')
        if j >= 0:
            key = line[:j].strip()
            val = line[j + 1:].strip()
            if key.startswith('MLC_'):
                env[key] = val

    return {'return': 0}
