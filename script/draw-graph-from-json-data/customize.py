from mlc import utils
import os


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    meta = i['meta']

    automation = i['automation']

    quiet = (env.get('MLC_QUIET', False) == 'yes')
    q = '"' if os_info['platform'] == 'windows' else "'"

    env['MLC_RUN_CMD'] = f"""{env['MLC_PYTHON_BIN_WITH_PATH']} {q}{os.path.join(env['MLC_TMP_CURRENT_SCRIPT_PATH'],"process-mlc-deps.py")}{q} {q}{env['MLC_JSON_INPUT_FILE']}{q} """

    if env.get('MLC_OUTPUT_IMAGE_PATH', '') != '':
        env['MLC_RUN_CMD'] += f""" --output_image {q}{env['MLC_OUTPUT_IMAGE_PATH']}{q} """

    if env.get('MLC_OUTPUT_MERMAID_PATH', '') != '':
        env['MLC_RUN_CMD'] += f""" --output_mermaid {q}{env['MLC_OUTPUT_MERMAID_PATH']}{q} """

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
