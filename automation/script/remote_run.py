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

    # Execute the experiment script
    mlc_script_input = {
        'action': 'run', 'target': 'script'
    }

    run_cmds = []
    remote_mlc_python_venv = i.get('remote_python_venv', 'mlcflow')
    run_cmds.append(f". {remote_mlc_python_venv}/bin/activate")
    if i.get('remote_pull_mlc_repos', False):
        run_cmds.append("mlc pull repo")

    script_run_cmd = " ".join(mlc_run_cmd.split(" ")[3:])
    run_cmds.append(f"mlcr {script_run_cmd}")

    remote_inputs = {}
    for key in ["host", "port", "user", "client_refresh",
                "password", "skip_host_verify", "ssh_key_file"]:
        if i.get(f"remote_{key}"):
            remote_inputs[key] = i[f"remote_{key}"]

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
