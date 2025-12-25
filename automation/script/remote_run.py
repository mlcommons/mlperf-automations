from collections import defaultdict
import os
import mlc.utils as utils
from mlc import utils
from utils import *
import logging
from pathlib import PureWindowsPath, PurePosixPath
import time
import copy
from datetime import datetime


def remote_run(self_module, i):
    """
    Remote run of MLC scripts.

    Args:
        self_module: Reference to the current module for internal calls.
        i: Dictionary containing input parameters for the experiment execution.

    Returns:
        Dictionary with the result of the operation. Keys:
        - 'return': 0 on success, >0 on error.
        - 'error': Error message (if any).
    """

    # Extract and handle basic inputs
    quiet = i.get('quiet', False)
    show_time = i.get('show_time', False)
    logger = self_module.logger
    env = i.get('env', {})
    remote_host = i.get('remote_host', 'localhost')
    remote_port = i.get('remote_port', 22)

    prune_result = prune_input(
        {'input': i, 'extra_keys_starts_with': ['remote_']})
    if prune_result['return'] > 0:
        return prune_result

    run_input = prune_result['new_input']
    mlc_run_cmd = run_input['mlc_run_cmd']

    cur_dir = os.getcwd()

    r = self_module._select_script(i)
    if r['return'] > 0:
        return r

    script = r['script']

    meta, script_path = script.meta, script.path
    tags, script_alias, script_uid = meta.get(
        "tags", []), meta.get(
        'alias', ''), meta.get(
        'uid', '')

    # Update meta for selected variation and input
    r = update_meta_for_selected_variations(self_module, script, i)
    if r['return'] > 0:
        return r

    remote_run_settings = r['remote_run_settings']
    env = r['env']

    # Execute the experiment script
    mlc_script_input = {
        'action': 'run', 'target': 'script'
    }

    run_cmds = []
    remote_mlc_python_venv = i.get('remote_python_venv', 'mlcflow')
    run_cmds.append(f". {remote_mlc_python_venv}/bin/activate")
    if i.get('remote_pull_mlc_repos', False):
        run_cmds.append("mlc pull repo")

    files_to_copy = []
    env_keys_to_copy = remote_run_settings.get('env_keys_to_copy', [])
    for key in env_keys_to_copy:
        if key in env and os.path.exists(env[key]):
            files_to_copy.append(env[key])

    script_run_cmd = " ".join(mlc_run_cmd.split(" ")[1:])
    run_cmds.append(f"mlcr {script_run_cmd}")

    remote_inputs = {}
    for key in ["host", "port", "user", "client_refresh",
                "password", "skip_host_verify", "ssh_key_file"]:
        if i.get(f"remote_{key}"):
            remote_inputs[key] = i[f"remote_{key}"]

    if files_to_copy:
        remote_inputs['files_to_copy'] = files_to_copy

    # Execute the remote command
    mlc_remote_input = {
        'action': 'run', 'target': 'script', 'tags': 'remote,run,cmds,ssh',
        'script_tags': i.get('tags'), 'run_cmds': run_cmds,
        **remote_inputs
    }

    r = self_module.action_object.access(mlc_remote_input)
    if r['return'] > 0:
        return r

    return {'return': 0}


def update_meta_for_selected_variations(self_module, script, input_params):
    metadata = script.meta
    script_directory = script.path
    script_tags = metadata.get("tags", [])
    script_alias = metadata.get('alias', '')
    script_uid = metadata.get('uid', '')
    tag_values = input_params.get('tags', '').split(",")
    variation_tags = [tag[1:] for tag in tag_values if tag.startswith("_")]

    run_state = {
        'deps': [],
        'fake_deps': [],
        'parent': None,
        'script_id': f"{script_alias},{script_uid}",
        'script_variation_tags': variation_tags
    }
    state_data = {}
    env = input_params.get('env', {})
    constant_vars = input_params.get('const', {})
    constant_state = input_params.get('const_state', {})

    remote_run_settings = metadata.get('remote_run', {})
    remote_run_settings_default_env = remote_run_settings.get(
        'default_env', {})
    for key in remote_run_settings_default_env:
        env.setdefault(key, remote_run_settings_default_env[key])

    state_data['remote_run'] = remote_run_settings
    add_deps_recursive = input_params.get('add_deps_recursive', {})

    # Update state with metadata and variations
    update_state_result = self_module.update_state_from_meta(
        metadata, env, state_data, constant_vars, constant_state,
        deps=[],
        post_deps=[],
        prehook_deps=[],
        posthook_deps=[],
        new_env_keys=[],
        new_state_keys=[],
        run_state=run_state,
        i=input_params
    )
    if update_state_result['return'] > 0:
        return update_state_result

    update_variations_result = self_module._update_state_from_variations(
        input_params, metadata, variation_tags, metadata.get(
            'variations', {}),
        env, state_data, constant_vars, constant_state,
        deps=[],  # Add your dependencies if needed
        post_deps=[],  # Add post dependencies if needed
        prehook_deps=[],  # Add prehook dependencies if needed
        posthook_deps=[],  # Add posthook dependencies if needed
        new_env_keys_from_meta=[],  # Add keys from meta if needed
        new_state_keys_from_meta=[],  # Add state keys from meta if needed
        add_deps_recursive=add_deps_recursive,
        run_state=run_state,
        recursion_spaces=''
    )
    if update_variations_result['return'] > 0:
        return update_variations_result

    # Set Docker-specific configurations
    remote_run_settings = state_data['remote_run']
    return {'return': 0, 'remote_run_settings': remote_run_settings,
            'env': env, 'state': state_data}
