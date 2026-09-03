from mlc import utils
from utils import is_true
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

    # With _lstopo, get,lstopo runs as a prehook dep and parks this node's
    # topology beside the sysinfo JSON, sharing its stem:
    #   mlperf-system-info-single-node-3.json
    #   mlperf-system-info-single-node-3.lstopo.xml
    # The shared stem is the contract generate-infograph pairs on, and it is
    # what lets get-mlperf-multi-node-system-info predict the remote filename
    # it has to copy back without a second round trip. Both keys are set only
    # when the capture is enabled, so a plain run exports nothing about a
    # topology it never took.
    if is_true(env.get('MLC_COLLECT_LSTOPO_TOPOLOGY', False)):
        info_path = env['MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH']
        xml_path = os.path.splitext(info_path)[0] + '.lstopo.xml'
        env['MLC_SINGLE_NODE_LSTOPO_XML_FILE_NAME'] = os.path.basename(xml_path)
        env['MLC_SINGLE_NODE_LSTOPO_XML_FILE_PATH'] = xml_path

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

    # Only advertise the topology path if the capture actually happened --
    # a dangling path reads as "there is a topology here" to callers.
    xml_path = env.get('MLC_SINGLE_NODE_LSTOPO_XML_FILE_PATH', '')
    if xml_path and not os.path.isfile(xml_path):
        automation.logger.warning(
            f"_lstopo was requested but no topology was written to "
            f"{xml_path}; this node will have no entry in the "
            f"infrastructure graph.")
        del env['MLC_SINGLE_NODE_LSTOPO_XML_FILE_PATH']

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
