from collections import defaultdict
import os
from mlc.main import ExperimentAction
import mlc.utils as utils
from mlc import utils
from utils import *
import logging
from pathlib import PureWindowsPath, PurePosixPath
import copy


def experiment_run(self_module, i):
    """
    Automates the exploration runs of MLC scripts.

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
    experiment_action = ExperimentAction(self_module.action_object.parent)

    prune_result = prune_input(
        {'input': i, 'extra_keys_starts_with': ['exp.']})
    if prune_result['return'] > 0:
        return prune_result

    run_input = prune_result['new_input']
    if run_input.get('exp'):
        del (run_input['exp'])

    r = convert_input(i)
    if r.get('exp'):
        exp = r['exp']
    else:
        exp = {}

    cur_dir = os.getcwd()
    r = self_module.search(i.copy())
    if r['return'] > 0:
        return r

    lst = r['list']
    if not lst:
        return {'return': 1, 'error': 'No scripts were found'}

    # Process each artifact
    for artifact in sorted(lst, key=lambda x: x.meta.get('alias', '')):
        meta, script_path = artifact.meta, artifact.path
        tags, script_alias, script_uid = meta.get(
            "tags", []), meta.get(
            'alias', ''), meta.get(
            'uid', '')

        # Execute the experiment script
        mlc_script_input = {
            'action': 'run', 'target': 'script'
        }
        if exp:
            for key in exp:
                ii = {**mlc_script_input, **run_input}
                if isinstance(exp[key], list):
                    for val in exp[key]:
                        ii[key] = val
                        r = self_module.action_object.access(ii)
                        if r['return'] > 0:
                            return r
                elif isinstance(exp[key], dict):
                    return {
                        'return': 1, 'error': 'Dictionary inputs are not supported for mlc experiment script'}
                else:
                    ii[key] = exp[key]
                    r = self_module.action_object.access(ii)
                    if r['return'] > 0:
                        return r

            experiment_meta = {}
            exp_tags = tags
            ii = {'action': 'update',
                  'target': 'experiment',
                  'script_alias': meta['alias'],
                  'tags': ','.join(exp_tags),
                  'meta': experiment_meta,
                  'force': True}
            r = experiment_action.access(ii)
            if r['return'] > 0:
                return r

    return {'return': 0}


def parse_value(val):
    if isinstance(val, list):
        return [parse_value(v) for v in val]

    val = str(val)

    # Handle range inputs like 2:10 or 2:10:2
    if ':' in val:
        parts = val.split(':')
        try:
            parts = list(map(int, parts))
            if len(parts) == 2:
                return list(range(parts[0], parts[1] + 1))
            elif len(parts) == 3:
                return list(range(parts[0], parts[1] + 1, parts[2]))
        except ValueError:
            pass  # Not a valid range, fall through

    # Convert to int if possible
    if val.isdigit():
        return int(val)

    return val


def convert_input(input_dict):
    output = defaultdict(dict)

    for key, value in input_dict.items():
        if '.' in key:
            main_key, sub_key = key.split('.', 1)
            output[main_key][sub_key] = parse_value(value)
        elif isinstance(value, dict):
            output[key].update({k: parse_value(v) for k, v in value.items()})

    return dict(output)
