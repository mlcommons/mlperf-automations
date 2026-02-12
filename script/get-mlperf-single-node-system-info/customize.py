from mlc import utils
import os
import subprocess

def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    if env.get('MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH', '') == '':
        if env.get('MLC_SINGLE_NODE_SYSTEM_INFO_DIR_PATH', '') == '':
            env['MLC_SINGLE_NODE_SYSTEM_INFO_DIR_PATH'] = os.getcwd()
        if env.get('MLC_SINGLE_NODE_SYSTEM_INFO_FILE_NAME', '') == '':
            env['MLC_SINGLE_NODE_SYSTEM_INFO_FILE_NAME'] = f"mlperf-system-info-single-node-{env.get('MLC_SINGLE_NODE_SYSTEM_ID', '')}.json"
        env['MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH'] = os.path.join(
            env['MLC_SINGLE_NODE_SYSTEM_INFO_DIR_PATH'], env['MLC_SINGLE_NODE_SYSTEM_INFO_FILE_NAME'])    

    if not os.path.exists(env['MLC_SINGLE_NODE_SYSTEM_INFO_DIR_PATH']):
        os.makedirs(env['MLC_SINGLE_NODE_SYSTEM_INFO_DIR_PATH'], exist_ok=True)

    CMD = """{MLC_PYTHON_BIN_WITH_PATH} {MLC_TMP_CURRENT_SCRIPT_PATH}/parse.py --input {MLC_PLATFORM_DETAILS_FILE_PATH} --output {MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH}"""

    env['MLC_RUN_CMD'] = CMD

    return {'return': 0}


def postprocess(i):

    state = i['state']

    env = i['env']

    os_info = i['os_info']

    automation = i['automation']

    return {'return': 0}
