from mlc import utils
from utils import *
import os
import mlc
import subprocess
import json


def preprocess(i):

    os_info = i['os_info']
    env = i['env']

    logger = i['automation'].logger

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

    if env.get('MLC_MULTINODE_SYSTEM_SSH_IDS', '') == '' and is_true(
            env.get('MLC_EXCLUDE_CURRENT_NODE', False)):
        return {'return': 1, 'error': 'Either MLC_EXCLUDE_CURRENT_NODE should be False or MLC_MULTINODE_SYSTEM_SSH_IDS should be provided'}
    elif env.get('MLC_MULTINODE_SYSTEM_SSH_IDS', '') != '':
        # set the run state dictionary to copy back the single node system info to all nodes after remote runs are done
        if not 'run_state' in i:
            i['run_state'] = {}
        run_state = i['run_state']
        if not 'remote_run' in run_state:
            run_state['remote_run'] = {}
        run_state['remote_run']['env_keys_to_copy_back'] = []
        run_state['remote_run']['env_keys_to_copy_back'].append('MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH')
        i['run_state'] = run_state

        # set remote run tags
        rr_tags = "get,mlperf,single-node,system-info"
        if env.get('MLC_ACCELERATOR_BACKEND', '') == 'cuda':
            rr_tags += ",_cuda"
        ssh_ids = [
            s.strip() for s in env['MLC_MULTINODE_SYSTEM_SSH_IDS'].split(',') if s.strip()]
        
        env['MLC_REMOTE_RUN_SSH_ID_COUNT'] = len(ssh_ids)

        for index, sshid in enumerate(ssh_ids):
            sshid_parts = [part.strip()
                           for part in sshid.split(':') if part.strip()]
            id = sshid_parts[0]
            if len(sshid_parts) > 1:
                port = sshid_parts[1]
            else:
                port = '22'  # default SSH port
            sshid_parts = [part.strip() for part in sshid_parts[0].split('@') if part.strip()]
            if len(sshid_parts) > 1:
                user = sshid_parts[0]
                host = sshid_parts[1]
            else:
                host = id
                user = "user"
            r = mlc.access({
                'action': 'remote_run',
                'automation': 'script',
                'tags': rr_tags,
                'run_cmd': f"{rr_tags}",
                'mlc_run_cmd': f"mlcr {rr_tags}",
                'node_id': index,
                'out_dir_path': f"/tmp/mlperf-system-info-single-node",
                'remote_host': host,
                'remote_user': user,
                'remote_port': port,
                'files_to_copy_back': [f"/tmp/mlperf-system-info-single-node/mlperf-system-info-single-node-{index}.json"],
                'path_to_copy_back_files': env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'],
                'run_state': run_state,
                'skip_ssh_key_file': env.get('MLC_SKIP_SSH_KEY_FILE', ''),
                'quiet': True,
                # 'remote_pull_mlc_repos': True
            })

            if r['return'] > 0:
                logger.error(f"Error obtaining information from remote node {sshid}!")
            else:
                logger.info(f"Successfully obtained information from remote node {sshid}")

    return {'return': 0}


def postprocess(i):

    state = i['state']

    env = i['env']

    os_info = i['os_info']

    logger = i['automation'].logger

    organization_metadata = {
        "submitter_org_name": env.get("MLC_MLPERF_SUBMITTER", "Insert your organization name here"),
        "submitter_contact": env.get("MLC_MLPERF_SUBMITTER_CONTACT", "Insert a contact email here"),
        "submission_id": env.get("MLC_MLPERF_SUBMISSION_ID", "Insert submission ID here"),
        "submission_date": env.get("MLC_MLPERF_SUBMISSION_DATE", ""),
        "publish_date": env.get("MLC_MLPERF_PUBLISH_DATE", ""),
    }

    sut = {
        "system_metadata": {
            "system_name": env.get("MLC_MLPERF_SYSTEM_NAME", "Insert system name here"),
            "system_category": env.get("MLC_MLPERF_SUBMISSION_SYSTEM_TYPE", "Insert system category here"),
            "system_type_detail": env.get("MLC_MLPERF_SUBMISSION_SYSTEM_TYPE_DETAIL", "Insert system type detail here"),
            "system_node_ensemble_total": env['MLC_REMOTE_RUN_SSH_ID_COUNT'],
            "system_availability_status": env.get("MLC_MLPERF_SUBMISSION_SYSTEM_STATUS", "Insert system availability status here"),
        },
    }

    model_metadata = {
        "division": env.get("MLC_MLPERF_SUBMISSION_DIVISION", "Insert model division here"),
        "model_id": env.get("MLC_MLPERF_MODEL_ID", "Insert model id here"),
        "model_name": env.get("MLC_MLPERF_MODEL", "Insert model name here"),
        "model_precision": env.get("MLC_MLPERF_MODEL_PRECISION", "Insert model precision here"),
        "link_to_model": env.get("MLC_MLPERF_MODEL_LINK", "Insert link to model here"),
        "link_to_model_transformations": env.get("MLC_MLPERF_MODEL_TRANSFORMATIONS_LINK", "Insert link to model transformations here"),
        "model_notes": env.get("MLC_MLPERF_MODEL_NOTES", "Insert any relevant notes about the model here"),
    }

    dataset_metadata = {
        "dataset_id": env.get("MLC_MLPERF_DATASET_ID", "Insert dataset name here"),
        "dataset_name": env.get("MLC_MLPERF_DATASET_NAME", "Insert dataset name here"),
        "input_token_average": env.get("MLC_MLPERF_DATASET_INPUT_TOKEN_AVERAGE", "Insert dataset input token average here"),
        "output_token_average": env.get("MLC_MLPERF_DATASET_OUTPUT_TOKEN_AVERAGE", "Insert dataset output token average here"),
        "dataset_type": env.get("MLC_MLPERF_DATASET_TYPE", "Insert dataset type here"),
        "dataset_link": env.get("MLC_MLPERF_DATASET_LINK", "Insert link to dataset here"),
    }

    parsed_node_details = []

    def update_parsed_node_details(node_id):
        node_details = {}
        single_node_system_info_path = os.path.join(
            env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'], f"mlperf-system-info-single-node-{node_id}.json")
        if os.path.exists(single_node_system_info_path):
            with open(single_node_system_info_path) as f:
                single_node_system_info = json.load(f)
        node_details['system_node_ensemble_id'] = node_id
        node_details['number_of_nodes'] = 1
        node_details['system_node_name'] = f"{single_node_system_info['hardware_ensemble']['processor'].get('host_processor_model_name', '')}-{single_node_system_info['hardware_ensemble']['accelerator'].get('accelerator_model_name', '')}"
        node_details['hardware_ensemble'] = single_node_system_info['hardware_ensemble']
        node_details['software_ensemble'] = single_node_system_info['software_ensemble']


        # ---- Check for duplicate system_node_name ----
        existing_entry = next(
            (entry for entry in parsed_node_details
            if entry['system_node_name'] == node_details['system_node_name']),
            None
        )
        if existing_entry:
            # Increment node count
            existing_entry['number_of_nodes'] += 1
        else:
            parsed_node_details.append(node_details)
    
    # Scenario where the host system is not being excluded
    if not is_true('MLC_EXCLUDE_CURRENT_NODE', False):
        logger.info("Obtaining system information from the host system")
        update_parsed_node_details(node_id="current")

    # For systems other than the host system
    logger.info("Obtaining system information from the remote systems")
    for node_id in range(int(env['MLC_REMOTE_RUN_SSH_ID_COUNT'])):
        update_parsed_node_details(node_id=node_id)

    sut['node_types'] = parsed_node_details

    parsed_multinode_system_info = {
        "organization_metadata": organization_metadata,
        "system_under_test": sut,
        "model_metadata": model_metadata,
        "dataset_metadata": dataset_metadata,    
    }

    try:
        with open(env['MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH'], 'w') as f:
            json.dump(parsed_multinode_system_info, f, indent=2)
        logger.info("Successfully compiled the system informtion")
    except Exception as e:
        logger.error(f"Exception {e} occured when compiling the system information")
            
    return {'return': 0}
