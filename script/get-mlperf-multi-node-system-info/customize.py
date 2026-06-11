from mlc import utils
from utils import *
import os
import re
import mlc
import subprocess
import json
import yaml


# Maps JSON config file keys to the env vars they populate.
# CLI args (already resolved into env vars by MLC) take precedence:
# a key from the config file is only applied when the env var is still empty.
_CONFIG_KEY_TO_ENV = {
    "submitter_org_names": "MLC_MLPERF_SUBMITTER",
    "submitter_contact": "MLC_MLPERF_SUBMITTER_CONTACT",
    "system_name": "MLC_MLPERF_SYSTEM_NAME",
    "system_category": "MLC_MLPERF_SUBMISSION_SYSTEM_TYPE",
    "system_availability_status": "MLC_MLPERF_SUBMISSION_SYSTEM_STATUS",
    "system_size": "MLC_MLPERF_SYSTEM_SIZE",
    "serving_framework": "MLC_MLPERF_SERVING_FRAMEWORK",
    "division": "MLC_MLPERF_SUBMISSION_DIVISION",
    "model_id": "MLC_MLPERF_MODEL_ID",
    "model_name": "MLC_MLPERF_MODEL",
    "model_precision": "MLC_MLPERF_MODEL_PRECISION",
    "link_to_model": "MLC_MLPERF_MODEL_LINK",
    "link_to_model_transformation": "MLC_MLPERF_MODEL_TRANSFORMATION_LINK",
    "model_notes": "MLC_MLPERF_MODEL_NOTES",
    "dataset_id": "MLC_MLPERF_DATASET_ID",
    "dataset_name": "MLC_MLPERF_DATASET_NAME",
    "dataset_type": "MLC_MLPERF_DATASET_TYPE",
    "input_token_average": "MLC_MLPERF_DATASET_INPUT_TOKEN_AVERAGE",
    "output_token_average": "MLC_MLPERF_DATASET_OUTPUT_TOKEN_AVERAGE",
    "dataset_link": "MLC_MLPERF_DATASET_LINK",
    "other_hardware": "MLC_MLPERF_OTHER_HARDWARE",
    "hw_notes": "MLC_MLPERF_HARDWARE_NOTES",
    "cooling": "MLC_MLPERF_COOLING",
    "container_link": "MLC_MLPERF_CONTAINER_LINK",
    "measured_accuracy_score": "MLC_MLPERF_MEASURED_ACCURACY_SCORE",
}


def _load_config_file(config_file, env, logger):
    """Load a JSON/YAML config file and populate env vars for any key not already set by CLI."""
    if not config_file or not os.path.exists(config_file):
        if config_file:
            logger.error(f"Config file not found: {config_file}")
        return
    try:
        with open(config_file) as f:
            if config_file.endswith(('.yaml', '.yml')):
                cfg = yaml.safe_load(f)
            else:
                cfg = json.load(f)
        applied = []
        for cfg_key, env_key in _CONFIG_KEY_TO_ENV.items():
            if not env.get(env_key) and cfg.get(cfg_key) is not None:
                env[env_key] = str(cfg[cfg_key])
                applied.append(cfg_key)
        logger.info(f"Loaded config from {config_file}" +
                    (f": applied {applied}" if applied else " (all fields already set by CLI)"))
    except Exception as e:
        logger.error(f"Failed to load config file {config_file}: {e}")


def _probe_serving_framework(url):
    """HTTP probe to detect vLLM, SGLang, or TRT-LLM from a running endpoint."""
    import urllib.request
    import json as _json
    base = url.rstrip('/')
    # TRT-LLM: /perf_metrics is unique to TRT-LLM (absent in vLLM and SGLang)
    try:
        with urllib.request.urlopen(f"{base}/perf_metrics", timeout=5) as _r:
            _r.read()
        try:
            with urllib.request.urlopen(f"{base}/version", timeout=5) as r2:
                vd = _json.loads(r2.read())
                if isinstance(vd, dict) and 'version' in vd:
                    return f"TRT-LLM {vd['version']}"
        except Exception:
            pass
        return 'TRT-LLM'
    except Exception:
        pass
    # vLLM: /version returns {"version": "x.y.z"}
    try:
        with urllib.request.urlopen(f"{base}/version", timeout=5) as r:
            d = _json.loads(r.read())
            if isinstance(d, dict) and 'version' in d:
                return f"vLLM {d['version']}"
    except Exception:
        pass
    # SGLang: /get_server_info
    try:
        with urllib.request.urlopen(f"{base}/get_server_info", timeout=5) as r:
            d = _json.loads(r.read())
            if isinstance(d, dict):
                v = d.get('version') or d.get(
                    'server_version') or d.get('sglang_version') or ''
                return f"SGLang {v}".rstrip() if v else 'SGLang'
    except Exception:
        pass
    return ''


def _parse_node(node_str):
    """Parse 'user@host:port' into (user, host, port) with sensible defaults."""
    parts = [p.strip() for p in node_str.split(':') if p.strip()]
    port = parts[1] if len(parts) > 1 else '22'
    at_parts = [p.strip() for p in parts[0].split('@') if p.strip()]
    if len(at_parts) > 1:
        user, host = at_parts[0], at_parts[1]
    else:
        host = parts[0]
        user = 'user'
    return user, host, port


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

    _load_config_file(env.get('MLC_MLPERF_CONFIG_FILE', ''), env, logger)

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
        backend = env.get('MLC_ACCELERATOR_BACKEND', '')
        if backend in ('cuda', 'rocm', 'xpu'):
            rr_tags += f",_{backend}"
        ssh_ids = [
            s.strip() for s in env['MLC_MULTINODE_SYSTEM_SSH_IDS'].split(',') if s.strip()]

        env['MLC_REMOTE_RUN_SSH_ID_COUNT'] = len(ssh_ids)

        exclude_current = is_true(env.get('MLC_EXCLUDE_CURRENT_NODE', False))
        remote_node_id_start = 0 if exclude_current else 1

        for index, sshid in enumerate(ssh_ids):
            user, host, port = _parse_node(sshid)
            actual_node_id = remote_node_id_start + index
            try:
                r = mlc.access({
                    'action': 'remote_run',
                    'automation': 'script',
                    'tags': rr_tags,
                    'run_cmd': f"{rr_tags}",
                    'mlc_run_cmd': f"mlcr {rr_tags}",
                    'node_id': actual_node_id,
                    'out_dir_path': f"/tmp/mlperf-system-info-single-node",
                    'remote_host': host,
                    'remote_user': user,
                    'remote_port': port,
                    'files_to_copy_back': [f"/tmp/mlperf-system-info-single-node/mlperf-system-info-single-node-{actual_node_id}.json"],
                    'path_to_copy_back_files': env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'],
                    'run_state': run_state,
                    'skip_ssh_key_file': env.get('MLC_SKIP_SSH_KEY_FILE', ''),
                    'quiet': True,
                })
                if r['return'] > 0:
                    logger.error(
                        f"Error obtaining information from remote node {sshid}!")
                else:
                    logger.info(
                        f"Successfully obtained information from remote node {sshid}")
            except Exception as e:
                logger.error(
                    f"Exception during remote_run for node {sshid}: {e}")

    serving_node = env.get('MLC_MLPERF_SERVING_NODE', '')
    if serving_node:
        user, host, port = _parse_node(serving_node)
        remote_out = '/tmp/mlperf-serving-config'
        sc_tags = 'get,mlperf,serving-config'
        try:
            r_sc = mlc.access({
                'action': 'remote_run',
                'automation': 'script',
                'tags': sc_tags,
                "run_cmd": f"{sc_tags}",
                'mlc_run_cmd': f'mlcr {sc_tags}',
                'remote_host': host,
                'remote_user': user,
                'remote_port': port,
                'log_path': env.get('MLC_MLPERF_SERVING_LOG_PATH', ''),
                'out_dir_path': remote_out,
                'files_to_copy_back': [f'{remote_out}/serving_config.json'],
                'path_to_copy_back_files': env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'],
                'skip_ssh_key_file': env.get('MLC_SKIP_SSH_KEY_FILE', ''),
                'serving_framework_type': env.get('MLC_MLPERF_SERVING_FRAMEWORK_TYPE', 'auto'),
                'quiet': True,
            })
            if r_sc['return'] > 0:
                logger.error(
                    f"Error obtaining serving config from {serving_node}")
            else:
                logger.info(
                    f"Successfully obtained serving config from {serving_node}")
        except Exception as e:
            logger.error(
                f"Exception during serving config remote_run for {serving_node}: {e}")

    endpoint_url = env.get('MLC_MLPERF_ENDPOINT_URL', '')
    if endpoint_url and not env.get('MLC_MLPERF_SERVING_FRAMEWORK', ''):
        detected = _probe_serving_framework(endpoint_url)
        if detected:
            env['MLC_MLPERF_SERVING_FRAMEWORK'] = detected
            logger.info(
                "Detected serving framework via HTTP probe: %s",
                detected)
        else:
            logger.info(
                "Could not detect serving framework from %s",
                endpoint_url)

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

    Returns (node_types, system_size, system_name, errors). On validation failure,
    all three output values are None and errors is a non-empty list.
    """
    all_yaml_node_names = []
    for func_nodes in node_config.values():
        for entry in func_nodes:
            name = entry.get("node_name", "")
            if name and name not in all_yaml_node_names:
                all_yaml_node_names.append(name)

    # Map YAML node_name → hardware/software details and probed count
    yaml_name_to_details = {}
    yaml_name_to_probed_count = {}
    for node_detail in parsed_node_details:
        accel_name = node_detail.get("accelerator_model_name", "")
        matched = _match_node_name(accel_name, all_yaml_node_names)
        if matched and matched not in yaml_name_to_details:
            yaml_name_to_details[matched] = node_detail
            yaml_name_to_probed_count[matched] = node_detail.get(
                "number_of_nodes", 1)
            logger.info(
                f"Matched single-node result ('{accel_name}') → YAML node '{matched}'")

    # Aggregate total declared no_of_nodes per unique node_name across all
    # functions
    declared_per_name = {}
    for func_nodes in node_config.values():
        for entry in func_nodes:
            name = entry.get("node_name", "")
            declared_per_name[name] = declared_per_name.get(
                name, 0) + int(entry.get("no_of_nodes", 1))

    # Validate declared counts against probed counts
    errors = []
    for name, declared_total in declared_per_name.items():
        if name not in yaml_name_to_probed_count:
            errors.append(
                f"node_name '{name}' declared in node_config has no matching probed node. "
                f"Ensure an SSH target with a '{name}' GPU was included and info was collected successfully."
            )
        else:
            probed_count = yaml_name_to_probed_count[name]
            if declared_total > probed_count:
                errors.append(
                    f"node_config declares {declared_total} '{name}' node(s) across all function groups "
                    f"but only {probed_count} '{name}' node(s) were probed. "
                    f"Add {declared_total - probed_count} more SSH ID(s) for this node type "
                    f"or adjust no_of_nodes in node_config."
                )

    if errors:
        return None, None, None, errors

    node_types = []
    ensemble_id = 1
    node_type_totals = {}

    for func_key, func_nodes in node_config.items():
        for entry in func_nodes:
            node_name = entry.get("node_name", "")
            no_of_nodes = int(entry.get("no_of_nodes", 1))
            combined_name = f"{node_name}({func_key})"

            details = yaml_name_to_details[node_name]

            node_type = {
                "system_node_ensemble_id": ensemble_id,
                "number_of_nodes": no_of_nodes,
            }
            node_type.update(
                {k: v for k, v in details.items()
                 if k not in {"system_node_ensemble_id", "number_of_nodes", "system_node_name"}}
            )

            node_types.append(node_type)
            node_type_totals[combined_name] = node_type_totals.get(
                combined_name, 0) + no_of_nodes
            ensemble_id += 1

    # system_name: config-derived labels with function (e.g. "1x
    # L40S(Prefill)")
    system_name = " + ".join(
        f"{count}x {name}" for name, count in node_type_totals.items())

    system_size = _compute_system_size(node_types)

    return node_types, system_size, system_name, []


def _is_not_detected(val):
    """Return True if val is a detection-failure reason string or empty/zero."""
    if val is None or val == "" or val == 0:
        return True
    return isinstance(val, str) and val.lower().startswith("not detected")


def _compute_system_size(node_entries):
    """Compute system_size per MLPerf Per Submission Data Dictionary spec.

    For each node type: if accelerators are present, use
    (number_of_nodes × accelerators_per_node)x accelerator_model_name;
    otherwise use (number_of_nodes × host_processors_per_node)x
    host_processor_model_name. Parts joined with ' + '.
    """
    parts = []
    for entry in node_entries:
        n_nodes = entry.get("number_of_nodes", 1)
        accel_name = entry.get("accelerator_model_name", "")
        accel_per_node = entry.get("accelerators_per_node", 0)

        if not _is_not_detected(
                accel_name) and not _is_not_detected(accel_per_node):
            try:
                qty = n_nodes * int(accel_per_node)
            except (ValueError, TypeError):
                qty = n_nodes
            parts.append(f"{qty}x {accel_name}")
        else:
            cpu_name = entry.get("host_processor_model_name", "")
            cpu_per_node = entry.get("host_processors_per_node", 1)
            if not _is_not_detected(cpu_name):
                try:
                    qty = n_nodes * int(cpu_per_node)
                except (ValueError, TypeError):
                    qty = n_nodes
                parts.append(f"{qty}x {cpu_name}")
    return " + ".join(parts)


def _build_system_size_from_nodes(parsed_node_details):
    return _compute_system_size(parsed_node_details)


def postprocess(i):

    state = i['state']

    env = i['env']

    os_info = i['os_info']

    logger = i['automation'].logger

    parsed_node_details = []

    def update_parsed_node_details(node_id):
        single_node_system_info_path = os.path.join(
            env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'], f"mlperf-system-info-single-node-{node_id}.json")
        if not os.path.exists(single_node_system_info_path):
            logger.warning(
                f"Single-node info file not found: {single_node_system_info_path}")
            return
        with open(single_node_system_info_path) as f:
            single_node_system_info = json.load(f)
        system_node_name = (
            f"{single_node_system_info.get('host_processor_model_name', '')}"
            f"-{single_node_system_info.get('accelerators_per_node', '')}"
            f"x{single_node_system_info.get('accelerator_model_name', '')}"
        )
        existing_entry = next(
            (entry for entry in parsed_node_details
             if entry['system_node_name'] == system_node_name),
            None
        )
        if existing_entry:
            existing_entry['number_of_nodes'] += 1
        else:
            node_details = {
                'system_node_ensemble_id': node_id,
                'number_of_nodes': 1,
                'system_node_name': system_node_name,
            }
            node_details.update(single_node_system_info)
            parsed_node_details.append(node_details)

    exclude_current = is_true(env.get('MLC_EXCLUDE_CURRENT_NODE', False))
    remote_node_id_start = 0 if exclude_current else 1

    if not exclude_current:
        logger.info("Obtaining system information from the host system")
        update_parsed_node_details(node_id=0)

    logger.info("Obtaining system information from the remote systems")
    for idx in range(int(env.get('MLC_REMOTE_RUN_SSH_ID_COUNT', 0))):
        update_parsed_node_details(node_id=remote_node_id_start + idx)

    # Apply node_config YAML if provided
    node_config_file = env.get("MLC_NODE_CONFIG_FILE", "")
    node_config = _load_node_config(node_config_file, logger)

    if node_config:
        node_types, system_size, system_name_from_config, errors = _build_node_types_from_yaml(
            node_config, parsed_node_details, logger)
        if errors:
            for err in errors:
                logger.error(err)
            return {'return': 1, 'error': '; '.join(errors)}
    else:
        node_types = parsed_node_details
        system_size = _build_system_size_from_nodes(parsed_node_details)
        system_name_from_config = system_size

    for nt in node_types:
        nt.pop("system_node_name", None)

    # Inject user-provided hardware/software metadata into each node type.
    # serving_framework is a system-level property lifted to the top of the
    # output, so strip it from each node entry to avoid duplication.
    other_hw = env.get("MLC_MLPERF_OTHER_HARDWARE", "")
    hw_notes = env.get("MLC_MLPERF_HARDWARE_NOTES", "")
    cooling = env.get("MLC_MLPERF_COOLING", "")
    container_link = env.get("MLC_MLPERF_CONTAINER_LINK", "")
    for node_type in node_types:
        node_type["other_hardware"] = other_hw
        node_type["hw_notes"] = hw_notes
        node_type["cooling"] = cooling
        node_type["container_link"] = container_link
        node_type.pop("serving_framework", None)

    serving_framework = env.get("MLC_MLPERF_SERVING_FRAMEWORK", "")
    user_system_name = env.get("MLC_MLPERF_SYSTEM_NAME", "")

    if not user_system_name:
        return {'return': 1, 'error': 'system_name is required. Set it via --system_name, the config file, or MLC_MLPERF_SYSTEM_NAME.'}

    parsed_multinode_system_info = {
        "submitter_org_names": env.get("MLC_MLPERF_SUBMITTER", "Insert your organization name here"),
        "submitter_contact": env.get("MLC_MLPERF_SUBMITTER_CONTACT", "Insert a contact email here"),
        "submission_id": "",
        "submission_date": "",
        "publish_date": "",
        "system_name": user_system_name,
        "system_category": env.get("MLC_MLPERF_SUBMISSION_SYSTEM_TYPE", "Insert system category here"),
        "system_availability_status": env.get("MLC_MLPERF_SUBMISSION_SYSTEM_STATUS", "Insert system availability status here"),
        "system_size": env.get("MLC_MLPERF_SYSTEM_SIZE", system_size),
        "system_node_ensemble_count": len(node_types),
        "system_node_ensemble_total": sum(entry['number_of_nodes'] for entry in node_types),
        "serving_framework": serving_framework,
        "node_types": node_types,
        "division": env.get("MLC_MLPERF_SUBMISSION_DIVISION", "Insert model division here"),
        "model_id": env.get("MLC_MLPERF_MODEL_ID", "Insert model id here"),
        "model_name": env.get("MLC_MLPERF_MODEL", "Insert model name here"),
        "model_precision": env.get("MLC_MLPERF_MODEL_PRECISION", "Insert model precision here"),
        "link_to_model": env.get("MLC_MLPERF_MODEL_LINK", "Insert link to model here"),
        "link_to_model_transformation": env.get("MLC_MLPERF_MODEL_TRANSFORMATION_LINK", "Insert link to model transformations here"),
        "model_notes": env.get("MLC_MLPERF_MODEL_NOTES", "Insert any relevant notes about the model here"),
        "dataset_id": env.get("MLC_MLPERF_DATASET_ID", "Insert dataset name here"),
        "dataset_name": env.get("MLC_MLPERF_DATASET_NAME", "Insert dataset name here"),
        "input_token_average": env.get("MLC_MLPERF_DATASET_INPUT_TOKEN_AVERAGE", "Insert dataset input token average here"),
        "output_token_average": env.get("MLC_MLPERF_DATASET_OUTPUT_TOKEN_AVERAGE", "Insert dataset output token average here"),
        "dataset_type": env.get("MLC_MLPERF_DATASET_TYPE", "Insert dataset type here"),
        "dataset_link": env.get("MLC_MLPERF_DATASET_LINK", "Insert link to dataset here"),
        "measured_accuracy_score": env.get("MLC_MLPERF_MEASURED_ACCURACY_SCORE", ""),
    }

    try:
        with open(env['MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH'], 'w') as f:
            json.dump(parsed_multinode_system_info, f, indent=2)
        logger.info("Successfully compiled the system informtion")
    except Exception as e:
        logger.error(
            f"Exception {e} occured when compiling the system information")

    # Patch run_metadata.yml config_summary with serving config values if
    # available.
    run_md_path = env.get('MLC_MLPERF_RUN_METADATA_PATH', '')
    serving_cfg_path = os.path.join(
        env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'], 'serving_config.json')
    if run_md_path and os.path.exists(
            serving_cfg_path) and os.path.exists(run_md_path):
        try:
            with open(serving_cfg_path) as f:
                sc = json.load(f)
            use_json = run_md_path.endswith('.json')
            with open(run_md_path) as f:
                run_md = json.load(f) if use_json else yaml.safe_load(f)
            for key in ('tensor_parallel', 'pipeline_parallel',
                        'expert_parallel', 'data_parallel', 'batch',
                        'disaggregated'):
                if sc.get(key) is not None:
                    run_md[key] = sc[key]
            if sc.get('config_summary'):
                run_md['config_summary'] = sc['config_summary']
            with open(run_md_path, 'w') as f:
                if use_json:
                    json.dump(run_md, f, indent=2)
                else:
                    yaml.dump(run_md, f, default_flow_style=False,
                              sort_keys=False, allow_unicode=True)
            logger.info("Patched run_metadata with serving config values")
            if not env.get('MLC_MLPERF_SERVING_FRAMEWORK') and sc.get(
                    'framework'):
                env['MLC_MLPERF_SERVING_FRAMEWORK'] = sc['framework']
                logger.info(
                    "Detected serving framework from log: %s",
                    sc['framework'])
        except Exception as e:
            logger.error(f"Failed to patch run_metadata.yml: {e}")

    return {'return': 0}
