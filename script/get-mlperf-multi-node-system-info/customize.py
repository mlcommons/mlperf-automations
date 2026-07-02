from utils import *
import os
import re
import mlc
import json
import yaml
import urllib.request


# Maps JSON/YAML config file keys to the env vars they populate.
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
    base = url.rstrip('/')
    # TRT-LLM: /perf_metrics is unique to TRT-LLM (absent in vLLM and SGLang)
    try:
        with urllib.request.urlopen(f"{base}/perf_metrics", timeout=5) as _r:
            _r.read()
        try:
            with urllib.request.urlopen(f"{base}/version", timeout=5) as r2:
                vd = json.loads(r2.read())
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
            d = json.loads(r.read())
            if isinstance(d, dict) and 'version' in d:
                return f"vLLM {d['version']}"
    except Exception:
        pass
    # SGLang: /get_server_info
    try:
        with urllib.request.urlopen(f"{base}/get_server_info", timeout=5) as r:
            d = json.loads(r.read())
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

    env = i['env']
    logger = i['automation'].logger

    if env.get('MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH', '') == '':
        if env.get('MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH', '') == '':
            env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'] = os.getcwd()
        if env.get('MLC_MULTI_NODE_SYSTEM_INFO_FILE_NAME', '') == '':
            env['MLC_MULTI_NODE_SYSTEM_INFO_FILE_NAME'] = "system-info-multi-node.json"
        env['MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH'] = os.path.join(
            env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'], env['MLC_MULTI_NODE_SYSTEM_INFO_FILE_NAME'])

    os.makedirs(env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH'], exist_ok=True)

    _load_config_file(env.get('MLC_MLPERF_CONFIG_FILE', ''), env, logger)

    if env.get('MLC_MULTINODE_SYSTEM_SSH_IDS', '') == '' and is_true(
            env.get('MLC_EXCLUDE_CURRENT_NODE', False)):
        return {'return': 1, 'error': 'Either MLC_EXCLUDE_CURRENT_NODE should be False or MLC_MULTINODE_SYSTEM_SSH_IDS should be provided'}
    elif env.get('MLC_MULTINODE_SYSTEM_SSH_IDS', '') != '':
        run_state = i.setdefault('run_state', {})
        run_state.setdefault('remote_run', {})['env_keys_to_copy_back'] = [
            'MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH']

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
                    'run_cmd': rr_tags,
                    'mlc_run_cmd': f"mlcr {rr_tags}",
                    'node_id': actual_node_id,
                    'out_dir_path': "/tmp/mlperf-system-info-single-node",
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
                'run_cmd': sc_tags,
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

    Returns (node_types, system_size, errors). On validation failure,
    both output values are None and errors is a non-empty list.
    """
    all_yaml_node_names = list(dict.fromkeys(
        entry.get("node_name", "")
        for func_nodes in node_config.values()
        for entry in func_nodes
        if entry.get("node_name", "")
    ))

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
        return None, None, errors

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

    system_size = _compute_system_size(node_types)

    return node_types, system_size, []


def _is_not_detected(val):
    """Return True if val is a detection-failure reason string or empty/zero."""
    if val is None or val == "" or val == 0:
        return True
    if isinstance(val, str):
        if val.lower().startswith("not detected"):
            return True
        # "N/A" and legacy "Not available" both signal auto-detection failure.
        if val in ("N/A", "Not available"):
            return True
        # A numeric-only string (e.g. "0") means the driver returned a device
        # index instead of a real name — treat as not detected.
        if val.strip().lstrip('-').isdigit():
            return True
    return False


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


# ── Inference flat-format helpers ───────────────────────────────────────

# Fields that are node-type metadata, not hardware fields to lift.
_NODE_METADATA_FIELDS = {
    "system_node_ensemble_id",
    "number_of_nodes",
    "system_node_name",
}

# Extra fields added when the 'network' variation is active alongside 'inference'.
# Matches SYSTEM_DESC_REQUIRED_FIELDS_NETWORK_MODE in
# submission_checker/constants.py.
_NETWORK_EXTRA_FIELDS = [
    "is_network",
    "network_type",
    "network_media",
    "network_rate",
    "nic_loadgen",
    "number_nic_loadgen",
    "net_software_stack_loadgen",
    "network_protocol",
    "number_connections",
    "nic_sut",
    "number_nic_sut",
    "net_software_stack_sut",
    "network_topology",
]

# Extra fields added when the 'power' variation is active alongside 'inference'.
# Matches SYSTEM_DESC_REQUIRED_FIELDS_POWER in submission_checker/constants.py.
# other_hardware is already in the base flat output.
_POWER_EXTRA_FIELDS = [
    "filesystem",
    "boot_firmware_version",
    "management_firmware_version",
    "number_of_type_nics_installed",
    "nics_enabled_firmware",
    "nics_enabled_os",
    "nics_enabled_connected",
    "network_speed_mbit",
    "power_supply_quantity_and_rating_watts",
    "power_supply_details",
    "disk_drives",
    "disk_controllers",
    "system_power_only",
]


def _is_homogeneous(node_types):
    """Return True if all node entries share the same hardware fingerprint."""
    if len(node_types) <= 1:
        return True
    ref_accel = node_types[0].get("accelerator_model_name", "")
    ref_cpu = node_types[0].get("host_processor_model_name", "")
    return all(
        nt.get("accelerator_model_name", "") == ref_accel and
        nt.get("host_processor_model_name", "") == ref_cpu
        for nt in node_types[1:]
    )


def _merge_heterogeneous_nodes(node_types):
    """Merge heterogeneous node types by comma-separating unique values per field."""
    all_fields = list(dict.fromkeys(
        k for nt in node_types for k in nt if k not in _NODE_METADATA_FIELDS
    ))

    merged = {}
    for field in all_fields:
        seen = []
        for nt in node_types:
            raw = nt.get(field, "")
            val = "" if raw is None else str(raw)
            if val and val not in seen:
                seen.append(val)
        merged[field] = ", ".join(seen)
    return merged


def _flatten_for_inference(nested_info, env):
    """
    Convert the nested node_types format to a flat dict compatible with the
    MLPerf Inference submission checker.

    Field name remappings applied at the top level:
      submitter_org_names        -> submitter
      system_availability_status -> status
      system_category            -> system_type
      serving_framework          -> framework

    Node-level hardware fields are lifted verbatim (no renames).
    All fields required by SYSTEM_DESC_REQUIRED_FIELDS in constants.py are present;
    those not auto-captured are set to empty string.
    """
    node_types = nested_info.get("node_types", [])
    total_nodes = nested_info.get(
        "system_node_ensemble_total",
        sum(nt.get("number_of_nodes", 1) for nt in node_types),
    )

    if not node_types:
        hw = {}
    elif _is_homogeneous(node_types):
        hw = {k: v for k, v in node_types[0].items(
        ) if k not in _NODE_METADATA_FIELDS}
    else:
        hw = _merge_heterogeneous_nodes(node_types)

    def _hw(key):
        """Return hw[key] as str, or '' when absent, None, 'Not available', or 'N/A'."""
        v = hw.get(key)
        if v is None or v in ("Not available", "N/A"):
            return ""
        return v

    flat = {
        # Identity / submitter
        "submitter": nested_info.get("submitter_org_names", ""),
        "submitter_contact": nested_info.get("submitter_contact", ""),
        "system_name": nested_info.get("system_name", ""),
        "status": nested_info.get("system_availability_status", ""),
        "system_type": nested_info.get("system_category", ""),
        "division": nested_info.get("division", ""),
        "system_size": nested_info.get("system_size", ""),
        # Multi-node count
        "number_of_nodes": total_nodes,
        # Host CPU
        "host_processor_model_name": _hw("host_processor_model_name"),
        "host_processors_per_node": _hw("host_processors_per_node"),
        "host_processor_core_count": _hw("host_processor_core_count"),
        "host_processor_vcpu_count": _hw("host_processor_vcpu_count"),
        "host_processor_frequency": _hw("host_processor_frequency"),
        "host_processor_caches": _hw("host_processor_caches"),
        "host_processor_interconnect": _hw("host_processor_interconnect"),
        # Host memory / storage
        "host_memory_capacity": _hw("host_memory_capacity"),
        "host_storage_type": _hw("host_storage_type"),
        "host_storage_capacity": _hw("host_storage_capacity"),
        "host_memory_configuration": _hw("host_memory_configuration"),
        # Host networking
        "host_networking": _hw("host_networking"),
        "host_networking_topology": "",  # requires manual input
        "host_network_card_count": _hw("host_network_card_count"),
        # Accelerator
        "accelerator_model_name": _hw("accelerator_model_name"),
        "accelerators_per_node": _hw("accelerators_per_node"),
        "accelerator_memory_capacity": _hw("accelerator_memory_capacity"),
        "accelerator_memory_configuration": _hw("accelerator_memory_configuration"),
        "accelerator_host_interconnect": _hw("accelerator_host_interconnect"),
        "accelerator_interconnect": _hw("accelerator_interconnect"),
        "accelerator_interconnect_topology": _hw("accelerator_interconnect_topology"),
        "accelerator_frequency": _hw("accelerator_frequency"),
        "accelerator_on-chip_memories": _hw("accelerator_on-chip_memories"),
        # Software
        "framework": nested_info.get("serving_framework", ""),
        "operating_system": _hw("operating_system"),
        "other_software_stack": _hw("other_software_stack"),
        # Notes / other
        "hw_notes": _hw("hw_notes"),
        "sw_notes": _hw("sw_notes"),
        "other_hardware": _hw("other_hardware"),
        "cooling": _hw("cooling"),
        "system_type_detail": "",  # requires manual input
    }

    if is_true(env.get("MLC_MLPERF_NETWORK_VARIATION", False)):
        flat.update({f: "" for f in _NETWORK_EXTRA_FIELDS if f not in flat})

    if is_true(env.get("MLC_MLPERF_POWER_VARIATION", False)):
        flat.update({f: "" for f in _POWER_EXTRA_FIELDS if f not in flat})

    return flat


def _update_parsed_node_details(
        node_id, dir_path, parsed_node_details, logger):
    """Load a single-node JSON file and merge it into parsed_node_details."""
    path = os.path.join(
        dir_path,
        f"mlperf-system-info-single-node-{node_id}.json")
    if not os.path.exists(path):
        logger.warning(f"Single-node info file not found: {path}")
        return
    with open(path) as f:
        info = json.load(f)
    node_name = (
        f"{info.get('host_processor_model_name', '')}"
        f"-{info.get('accelerators_per_node', '')}"
        f"x{info.get('accelerator_model_name', '')}"
    )
    existing = next(
        (e for e in parsed_node_details if e['system_node_name'] == node_name),
        None)
    if existing:
        existing['number_of_nodes'] += 1
    else:
        entry = {
            'system_node_ensemble_id': node_id,
            'number_of_nodes': 1,
            'system_node_name': node_name}
        entry.update(info)
        parsed_node_details.append(entry)


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger

    dir_path = env['MLC_MULTI_NODE_SYSTEM_INFO_DIR_PATH']
    parsed_node_details = []

    exclude_current = is_true(env.get('MLC_EXCLUDE_CURRENT_NODE', False))
    remote_node_id_start = 0 if exclude_current else 1

    if not exclude_current:
        logger.info("Obtaining system information from the host system")
        _update_parsed_node_details(0, dir_path, parsed_node_details, logger)

    logger.info("Obtaining system information from the remote systems")
    for idx in range(int(env.get('MLC_REMOTE_RUN_SSH_ID_COUNT', 0))):
        _update_parsed_node_details(
            remote_node_id_start + idx,
            dir_path,
            parsed_node_details,
            logger)

    node_config = _load_node_config(
        env.get("MLC_NODE_CONFIG_FILE", ""), logger)

    if node_config:
        node_types, system_size, errors = _build_node_types_from_yaml(
            node_config, parsed_node_details, logger)
        if errors:
            for err in errors:
                logger.error(err)
            return {'return': 1, 'error': '; '.join(errors)}
    else:
        node_types = parsed_node_details
        system_size = _compute_system_size(parsed_node_details)

    for nt in node_types:
        nt.pop("system_node_name", None)

    # Inject user-provided metadata into each node type.
    # serving_framework is a system-level property, so strip it from node
    # entries.
    node_meta = {
        "other_hardware": env.get("MLC_MLPERF_OTHER_HARDWARE", ""),
        "hw_notes": env.get("MLC_MLPERF_HARDWARE_NOTES", ""),
        "cooling": env.get("MLC_MLPERF_COOLING", ""),
        "container_link": env.get("MLC_MLPERF_CONTAINER_LINK", ""),
    }
    for node_type in node_types:
        node_type.update(node_meta)
        node_type.pop("serving_framework", None)

    user_system_name = env.get("MLC_MLPERF_SYSTEM_NAME", "")
    if not user_system_name:
        return {'return': 1, 'error': 'system_name is required. Set it via --system_name, the config file, or MLC_MLPERF_SYSTEM_NAME.'}

    output_info = {
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
        "system_node_ensemble_total": sum(e['number_of_nodes'] for e in node_types),
        "serving_framework": env.get("MLC_MLPERF_SERVING_FRAMEWORK", ""),
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

    if env.get("MLC_MLPERF_BENCHMARK", "") == "inference":
        output_info = _flatten_for_inference(output_info, env)
        logger.info("Using flat inference format for system_info.json")

    try:
        with open(env['MLC_MULTI_NODE_SYSTEM_INFO_FILE_PATH'], 'w') as f:
            json.dump(output_info, f, indent=2)
        logger.info("Successfully compiled the system information")
    except Exception as e:
        logger.error(
            f"Exception {e} occurred when compiling the system information")

    # Patch run_metadata (JSON or YAML) with serving config values if
    # available.
    run_md_path = env.get('MLC_MLPERF_RUN_METADATA_PATH', '')
    serving_cfg_path = os.path.join(dir_path, 'serving_config.json')
    if run_md_path and os.path.exists(
            serving_cfg_path) and os.path.exists(run_md_path):
        try:
            with open(serving_cfg_path) as f:
                sc = json.load(f)
            use_json = run_md_path.endswith('.json')
            with open(run_md_path) as f:
                run_md = json.load(f) if use_json else yaml.safe_load(f)
            for key in ('tensor_parallel', 'pipeline_parallel',
                        'expert_parallel', 'data_parallel', 'batch', 'disaggregated'):
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
            logger.error(f"Failed to patch {run_md_path}: {e}")

    return {'return': 0}
