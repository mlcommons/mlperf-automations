from mlc import utils
import os
import json
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

    CMD = f"""{env['MLC_PYTHON_BIN_WITH_PATH']} {env['MLC_TMP_CURRENT_SCRIPT_PATH']}/parse.py --output {env['MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH']}"""

    env['MLC_RUN_CMD'] = CMD

    return {'return': 0}


def postprocess(i):

    state = i['state']

    env = i['env']

    os_info = i['os_info']

    automation = i['automation']

    # Stamp the output with the git version of the automations repo that
    # produced it (traceability, since mlc-scripts has no tagged release).
    output_path = env.get('MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH', '')
    repo_path = env.get('MLC_TMP_CURRENT_SCRIPT_REPO_PATH', '')
    if output_path and os.path.exists(output_path):
        try:
            from mlc.utils import get_repo_version
            version = get_repo_version(repo_path)
            if version:
                with open(output_path) as f:
                    data = json.load(f)
                data['mlc_scripts_version'] = {
                    'repo': os.path.basename(repo_path), **version}
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            automation.logger.warning(
                f"Could not add version info to {output_path}: {e}")

    return {'return': 0}
