from mlc import utils
from utils import *
import os
import re
import mlc
import subprocess
import json
import yaml


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
        # set the run state dictionary to copy back the single node system info
        # to all nodes after remote runs are done
        if not 'run_state' in i:
            i['run_state'] = {}
        run_state = i['run_state']
        if not 'remote_run' in run_state:
            run_state['remote_run'] = {}
        run_state['remote_run']['env_keys_to_copy_back'] = []
        run_state['remote_run']['env_keys_to_copy_back'].append(
            'MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH')
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
            sshid_parts = [part.strip()
                           for part in sshid_parts[0].split('@') if part.strip()]
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
                logger.error(
                    f"Error obtaining information from remote node {sshid}!")
            else:
                logger.info(
                    f"Successfully obtained information from remote node {sshid}")

    return {'return': 0}


def _match_node_name(accelerator_model_name, yaml_node_names):
    """Match an accelerator model name against YAML node name candidates."""
    accel_lower = accelerator_model_name.lower()
    for node_name in yaml_node_names:
        if node_name.lower() in accel_lower:
            return node_name
        if re.search(r'\b' + re.escape(node_name) + r'\b',
                     accelerator_model_name, re.IGNORECASE):
            return node_name
    return None


def _load_node_config(node_config_file, logger):
    """Load and parse the node_config YAML file."""
    if not node_config_file or not os.path.exists(node_config_file):
        return None
    try:
        with open(node_config_file) as f:
            data = yaml.safe_load(f)
        return data.get("system_info", {}).get("node_config", {})
    except Exception as e:
        logger.error(
            f"Failed to load node_config file {node_config_file}: {e}")
        return None


def _build_node_types_from_yaml(node_config, parsed_node_details, logger):
    """
    Match detected single-node hardware to YAML node names and build the
    node_types list with function groupings and authoritative node counts.

    Returns (node_types, system_size).
    """
    all_yaml_node_names = []
    for func_nodes in node_config.values():
        for entry in func_nodes:
            name = entry.get("node_name", "")
            if name and name not in all_yaml_node_names:
                all_yaml_node_names.append(name)

    # Map YAML node_name → hardware/software details from single-node results
    yaml_name_to_details = {}
    for node_detail in parsed_node_details:
        accel_name = (node_detail
                      .get("hardware_ensemble", {})
                      .get("accelerator", {})
                      .get("accelerator_model_name", ""))
        matched = _match_node_name(accel_name, all_yaml_node_names)
        if matched and matched not in yaml_name_to_details:
            yaml_name_to_details[matched] = node_detail
            logger.info(
                f"Matched single-node result ('{accel_name}') → YAML node '{matched}'")

    node_types = []
    ensemble_id = 1
    node_type_totals = {}  # node_name → total count across all functions

    for func_key, func_nodes in node_config.items():
        for entry in func_nodes:
            node_name = entry.get("node_name", "")
            no_of_nodes = int(entry.get("no_of_nodes", 1))

            node_type = {
                "system_node_ensemble_id": ensemble_id,
                "function": func_key,
                "number_of_nodes": no_of_nodes,
                "system_node_name": node_name,
            }

            if node_name in yaml_name_to_details:
                details = yaml_name_to_details[node_name]
                node_type["hardware_ensemble"] = details.get(
                    "hardware_ensemble", {})
                node_type["software_ensemble"] = details.get(
                    "software_ensemble", {})
            else:
                logger.warning(
                    f"No single-node data found for YAML node '{node_name}'")

            node_types.append(node_type)
            node_type_totals[node_name] = node_type_totals.get(
                node_name, 0) + no_of_nodes
            ensemble_id += 1

    system_size_parts = [
        f"{count}x {name}" for name,
        count in node_type_totals.items()]
    system_size = " + ".join(system_size_parts)

    return node_types, system_size


def _build_system_size_from_nodes(parsed_node_details):
    """Compute system_size from detected node types when no YAML is provided."""
    parts = []
    for entry in parsed_node_details:
        n = entry.get("number_of_nodes", 1)
        node_name = entry.get("system_node_name", "")
        parts.append(f"{n}x({node_name})")
    return " + ".join(parts)


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
            "system_category": env.get("MLC_MLPERF_SUBMISSION_SYSTEM_TYPE", "Insert system category here"),
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
        node_details['system_node_name'] = f"{single_node_system_info['hardware_ensemble']['processor'].get('host_processor_model_name', '')}-{single_node_system_info['hardware_ensemble']['accelerator'].get('accelerators_per_node', '')}x{single_node_system_info['hardware_ensemble']['accelerator'].get('accelerator_model_name', '')}"
        node_details['hardware_ensemble'] = single_node_system_info['hardware_ensemble']
        node_details['software_ensemble'] = single_node_system_info['software_ensemble']

        existing_entry = next(
            (entry for entry in parsed_node_details
             if entry['system_node_name'] == node_details['system_node_name']),
            None
        )
        if existing_entry:
            existing_entry['number_of_nodes'] += 1
        else:
            parsed_node_details.append(node_details)

    exclude_current = is_true(env.get('MLC_EXCLUDE_CURRENT_NODE', False))
    remote_node_id_start = 0 if exclude_current else 1

    if not exclude_current:
        logger.info("Obtaining system information from the host system")
        update_parsed_node_details(node_id=0)

    logger.info("Obtaining system information from the remote systems")
    for idx in range(int(env['MLC_REMOTE_RUN_SSH_ID_COUNT'])):
        update_parsed_node_details(node_id=remote_node_id_start + idx)

    # Apply node_config YAML if provided
    node_config_file = env.get("MLC_NODE_CONFIG_FILE", "")
    node_config = _load_node_config(node_config_file, logger)

    if node_config:
        node_types, system_size = _build_node_types_from_yaml(
            node_config, parsed_node_details, logger)
    else:
        node_types = parsed_node_details
        system_size = _build_system_size_from_nodes(parsed_node_details)

    sut['node_types'] = node_types
    sut["system_metadata"]["system_size"] = env.get(
        "MLC_MLPERF_SYSTEM_SIZE", system_size)
    sut["system_metadata"]["system_node_ensemble_count"] = len(node_types)
    sut["system_metadata"]["system_node_ensemble_total"] = sum(
        entry['number_of_nodes'] for entry in node_types)

    # system_name: use explicit user input, or fall back to system_size
    user_system_name = env.get("MLC_MLPERF_SYSTEM_NAME", "")
    sut["system_metadata"]["system_name"] = user_system_name if user_system_name else system_size

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
        logger.error(
            f"Exception {e} occured when compiling the system information")

    return {'return': 0}
