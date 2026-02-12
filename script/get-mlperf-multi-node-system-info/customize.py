from mlc import utils
from automation.utils import is_true
from utils import *
import os
import mlc
import subprocess

def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    if env.get('MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH', '') == '':
        if env.get('MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH', '') == '':
            env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'] = os.getcwd()
        if env.get('MLC_MULTI_NODE_SYSTEM_INFO_FILE_NAME', '') == '':
            env['MLC_MULTI_NODE_SYSTEM_INFO_FILE_NAME'] = f"system-info-multi-node.json"
        env['MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH'] = os.path.join(
            env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'], env['MLC_MULTI_NODE_SYSTEM_INFO_FILE_NAME'])    
        
    # create the directory if not present
    if not os.path.exists(env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH']):
        os.makedirs(env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'], exist_ok=True)

    if env.get('MLC_MULTINODE_SYSTEM_SSH_IDS', '') == '' and is_true(env.get('MLC_EXCLUDE_CURRENT_NODE', False)):
        return {'return': 1, 'error': 'Either MLC_EXCLUDE_CURRENT_NODE should be False or MLC_MULTINODE_SYSTEM_SSH_IDS should be provided'}
    elif env.get('MLC_MULTINODE_SYSTEM_SSH_IDS', '') != '':
        # set the run state dictionary to copy back the single node system info to all nodes after remote runs are done
        run_state = i['run_script_inputs']['run_state']
        run_state['remote_run']['env_keys_to_copy_back'] = []
        run_state['remote_run']['env_keys_to_copy_back'].append('MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH')

        # set remote run tags
        rr_tags = "get-mlperf-single-node-system-info"
        if env.get('MLC_ACCELERATOR_BACKEND', '') == 'cuda':
            rr_tags += ",_cuda"
        ssh_ids = [s.strip() for s in env['MLC_MULTINODE_SYSTEM_SSH_IDS'].split(',') if s.strip()]
        
        for index, sshid in enumerate(ssh_ids):
            sshid_parts = [part.strip() for part in sshid.split(':') if part.strip()]
            id = sshid_parts[0]
            if len(sshid_parts) > 1:
                port = sshid_parts[1]
            else:
                port = '22'  # default SSH port
            r = mlc.access({
                'action': 'remote_run',
                'automation': 'script',
                'tags': rr_tags,
                'run_inputs': {
                    'node_id': index,
                    'out_dir_path': f"/tmp/mlperf-system-info-single-node",
                },
                'remote_host': id,
                'remote_port': port,
                'files_to_copy_back': [f"/tmp/mlperf-system-info-single-node/mlperf-system-info-single-node-{id}.json"],
                'path_to_copy_back_files': env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH']
            })

    # CMD = """{MLC_PYTHON_BIN_WITH_PATH} {MLC_TMP_CURRENT_SCRIPT_PATH}/parse_singe_nodes.py --input {MLC_PLATFORM_DETAILS_FILE_PATH} --output {MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH}"""

    # env['MLC_RUN_CMD'] = CMD

    return {'return': 0}


def postprocess(i):

    state = i['state']

    env = i['env']

    os_info = i['os_info']

    automation = i['automation']

    return {'return': 0}
