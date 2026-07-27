from mlc import utils
import os
import json
import subprocess


def scripts_version_block(env):
    """Assemble a provenance block from the MLC_TMP_SCRIPTS_GIT_* env vars set
    by the engine, identifying the automations repo commit that produced this
    output. Returns an empty dict when the engine did not provide version info."""
    source = env.get('MLC_TMP_SCRIPTS_GIT_VERSION_SOURCE', '')
    if not source:
        return {}
    block = {
        "repo": env.get('MLC_TMP_SCRIPTS_GIT_REPO', ''),
        "commit": env.get('MLC_TMP_SCRIPTS_GIT_COMMIT', ''),
        "branch": env.get('MLC_TMP_SCRIPTS_GIT_BRANCH', ''),
        "dirty": env.get('MLC_TMP_SCRIPTS_GIT_DIRTY', '') == 'true',
        "source": source,
    }
    package_version = env.get('MLC_TMP_SCRIPTS_PACKAGE_VERSION', '')
    if package_version:
        block["package_version"] = package_version
    return block


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

    logger = automation.logger

    # Stamp the output with the automations repo version that produced it.
    version_block = scripts_version_block(env)
    output_path = env.get('MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH', '')
    if version_block and output_path and os.path.exists(output_path):
        try:
            with open(output_path) as f:
                data = json.load(f)
            data['mlc_scripts_version'] = version_block
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(
                f"Could not add version info to {output_path}: {e}")

    return {'return': 0}
