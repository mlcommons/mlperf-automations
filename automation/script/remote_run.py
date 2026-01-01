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
from script.script_utils import *


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
    remote_port = i.get('remote_port', '22')

    prune_result = prune_input(
        {'input': i, 'extra_keys_starts_with': ['remote_']})
    if prune_result['return'] > 0:
        return prune_result

    run_input = prune_result['new_input']
    mlc_run_cmd = run_input['mlc_run_cmd']

    # print(script_cmd)
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

    remote_env = {}

    remote_run_settings = r['remote_run_settings']
    env = self_module.env
    state = self_module.state
    meta = r['meta']

    r = call_remote_run_prepare(self_module, meta, script, i)
    if r['return'] > 0:
        return r

    files_to_copy = r.get('files_to_copy', [])
    remote_env = r.get('remote_env', {})

    mlc_script_input = {
        'action': 'run', 'target': 'script'
    }

    run_cmds = []
    remote_mlc_python_venv = i.get('remote_python_venv', 'mlcflow')
    run_cmds.append(f". {remote_mlc_python_venv}/bin/activate")
    if i.get('remote_pull_mlc_repos', False):
        run_cmds.append("mlc pull repo")

    env_keys_to_copy = remote_run_settings.get('env_keys_to_copy', [])
    input_mapping = meta.get('input_mapping', {})

    for key in env_keys_to_copy:
        if key in env and os.path.exists(env[key]):
            files_to_copy.append(env[key])
            remote_env[key] = os.path.join(
                "mlc-remote-artifacts",
                os.path.basename(
                    env[key]))

            for k, value in input_mapping.items():
                if value == key and k in run_input:
                    run_input[k] = remote_env[key]

    i_copy = copy.deepcopy(i)
    i_copy['run_cmd'] = run_input

    r = regenerate_script_cmd(i_copy)
    if r['return'] > 0:
        return r

    # " ".join(mlc_run_cmd.split(" ")[1:])
    script_run_cmd = r['run_cmd_string']

    if remote_env:
        for key in remote_env:
            script_run_cmd += f" --env.{key}={remote_env[key]}"

    run_cmds.append(f"{script_run_cmd}")

    remote_inputs = {}

    for key in ["host", "port", "user", "client_refresh",
                "password", "skip_host_verify", "ssh_key_file", "copy_directory"]:
        if i.get(f"remote_{key}"):
            remote_inputs[key] = i[f"remote_{key}"]

    if files_to_copy:
        remote_copy_directory = i.get(
            "remote_copy_directory",
            "mlc-remote-artifacts")
        remote_inputs['files_to_copy'] = files_to_copy
        remote_inputs['copy_directory'] = remote_copy_directory

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

    if not has_attr(self_module, 'run_state'):
        self_module.run_state = self_module.init_run_state(input_params.get('run_state'))

    run_state = self_module.run_state

    run_state.update({
        'script_id': f"{script_alias},{script_uid}",
        'script_variation_tags': variation_tags
    }
    )

    remote_run_settings = metadata.get('remote_run', {})
    remote_run_settings_default_env = remote_run_settings.get(
        'default_env', {})
    for key in remote_run_settings_default_env:
        env.setdefault(key, remote_run_settings_default_env[key])

    run_state['remote_run'] = remote_run_settings
    add_deps_recursive = input_params.get('add_deps_recursive', {})

    # Update state with metadata and variations
    update_state_result = self_module.update_state_from_meta(
        metadata,
        run_state=run_state,
        i=input_params
    )
    if update_state_result['return'] > 0:
        return update_state_result

    update_variations_result = self_module._update_state_from_variations(
        input_params, metadata, variation_tags, metadata.get(
            'variations', {}), run_state=run_state
    )
    if update_variations_result['return'] > 0:
        return update_variations_result

    remote_run_settings = run_state['remote_run']
    return {'return': 0, 'remote_run_settings': remote_run_settings,
            'meta': metadata}


def call_remote_run_prepare(self_module, meta, script_item, i):

    path_to_customize_py = os.path.join(script_item.path, 'customize.py')
    logger = self_module.logger
    recursion_spaces = ''

    # Check and run remote_run_prepare in customize.py
    if os.path.isfile(path_to_customize_py) and has_function_in_file(
            path_to_customize_py, "remote_run_prepare"):

        customize_code = load_customize_with_deps(path_to_customize_py)

        customize_common_input = {
            'input': i,
            'automation': self_module,
            'artifact': script_item,
            # 'customize': script_item.meta.get('customize', {}),
            # 'os_info': os_info,
            # 'recursion_spaces': recursion_spaces,
            # 'script_tags': script_tags,
            # 'variation_tags': variation_tags
        }

        run_script_input = {
            "customize_code": customize_code,
            "customize_common_input": customize_common_input,
            "run_state": {},
        }

        ii = copy.deepcopy(customize_common_input)
        ii["meta"] = meta
        ii["env"] = self_module.env
        ii["state"] = self_module.state
        ii["automation"] = self_module
        ii["run_script_input"] = run_script_input

        return customize_code.remote_run_prepare(ii)

    return {'return': 0}


def regenerate_script_cmd(i):

    remote_run_settings = i.get('remote_run_settings', {})
    fake_run = i.get('fake_run', False)

    i_run_cmd = i['run_cmd']

    # Remove environment variables with host path values
    if 'env' in i_run_cmd:
        env = i_run_cmd['env']
        for key in list(env):
            value = env[key]

            # Check if the value is a string containing the specified paths
            if isinstance(value, str) and (
                    os.path.join("local", "cache", "") in value or
                    os.path.join("MLC", "repos", "") in value or
                    "<<<" in value
            ):
                del env[key]

            # Check if the value is a list and remove matching items
            elif isinstance(value, list):
                # Identify values to remove
                values_to_remove = [
                    val for val in value
                    if isinstance(val, str) and (
                        os.path.join("local", "cache", "") in val or
                        os.path.join("MLC", "repos", "") in val or
                        "<<<" in value
                    )
                ]

                # Remove key if all values match; otherwise, filter the list
                if len(values_to_remove) == len(value):
                    del env[key]
                else:
                    env[key] = [
                        val for val in value if val not in values_to_remove]

    # docker_run_cmd_prefix = i.get('docker_run_cmd_prefix', '')

    # Regenerate command from dictionary input
    run_cmd = 'mlcd' if i.get('docker') else 'mlcr'

    skip_input_for_fake_run = remote_run_settings.get(
        'skip_input_for_fake_run', [])
    add_quotes_to_keys = remote_run_settings.get('add_quotes_to_keys', [])

    def rebuild_flags(
            command_dict,
            is_fake_run,
            skip_keys_for_fake_run,
            quote_keys,
            prefix
    ):
        """
        Recursively rebuilds command-line flags from a dictionary of inputs.

        :param command_dict: Dictionary containing command-line keys and values.
        :param is_fake_run: Boolean indicating if this is a fake run.
        :param skip_keys_for_fake_run: List of keys to skip in fake run mode.
        :param quote_keys: List of keys that require values to be quoted.
        :param prefix: String to prepend to keys for hierarchical keys.
        :return: A reconstructed command-line string.
        """
        command_line = ""

        # Sort keys to ensure 'tags' appears first if present.
        keys = sorted(command_dict.keys(), key=lambda x: x != "tags")

        for key in keys:
            if key in ["input", "output", "outdirname"]:
                continue  # We have the corresponding env keys in container env string
            # Construct the full key with the prefix.
            full_key = f"{prefix}.{key}" if prefix else key

            # Skip keys marked for exclusion in fake run mode.
            if is_fake_run and full_key in skip_keys_for_fake_run:
                continue

            value = command_dict[key]
            quote = '"' if full_key in quote_keys else ""

            # Recursively process nested dictionaries.
            if isinstance(value, dict):
                command_line += rebuild_flags(
                    value,
                    is_fake_run,
                    skip_keys_for_fake_run,
                    quote_keys,
                    full_key
                )
            # Process lists by concatenating values with commas.
            elif isinstance(value, list):
                list_values = ",".join(
                    quote_if_needed(
                        item, quote) for item in value)
                command_line += f" --{full_key},={list_values}"
            # Process scalar values.
            else:
                if full_key in ['s', 'v']:
                    command_line += f" -{full_key}"
                else:
                    command_line += f" --{full_key}={quote_if_needed(value, quote)}"

        return command_line

    run_cmd += rebuild_flags(i_run_cmd,
                             fake_run,
                             skip_input_for_fake_run,
                             add_quotes_to_keys,
                             '')

    # run_cmd = docker_run_cmd_prefix + ' && ' + \
    #    run_cmd if docker_run_cmd_prefix != '' else run_cmd

    return {'return': 0, 'run_cmd_string': run_cmd}
