from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = (env.get('MLC_QUIET', False) == 'yes')

    env['MLC_RUN_CMD'] = f"""{env['MLC_PYTHON_BIN_WITH_PATH']} "{os.path.join(env['MLC_TMP_CURRENT_SCRIPT_PATH'],"process-mlc-deps.py")}" "{env['MLC_JSON_INPUT_FILE']}" """

    if env.get('MLC_OUTPUT_IMAGE_PATH', '') != '':
        env['MLC_RUN_CMD'] += f""" --output_image "{env['MLC_OUTPUT_IMAGE_PATH']}" """

    if env.get('MLC_OUTPUT_MERMAID_PATH', '') != '':
        env['MLC_RUN_CMD'] += f""" --output_mermaid "{env['MLC_OUTPUT_MERMAID_PATH']}" """

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
