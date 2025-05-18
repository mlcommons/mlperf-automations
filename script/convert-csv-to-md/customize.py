from mlc import utils
from utils import is_true
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = is_true(env.get('MLC_QUIET', False))

    csv_file = env.get('MLC_CSV_FILE', '')
    md_file = env.get('MLC_MD_FILE', '')
    process_file = os.path.join(i['run_script_input']['path'], "process.py")

    env['MLC_RUN_CMD'] = '{} {} {} {} '.format(
        env["MLC_PYTHON_BIN_WITH_PATH"], process_file, csv_file, md_file)

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
