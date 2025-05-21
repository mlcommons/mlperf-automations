from collections import defaultdict
import os
from mlc.main import ExperimentAction
import mlc.utils as utils
from mlc import utils
from utils import *
import logging
from pathlib import PureWindowsPath, PurePosixPath
import time
import copy
from datetime import datetime


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
    skip_state_save = i.get('exp_skip_state_save', False)
    extra_exp_tags = i.get('exp_tags', '').split(",")

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
                        r = run_script_and_tag_experiment(
                            ii,
                            self_module.action_object,
                            experiment_action,
                            tags,
                            extra_exp_tags,
                            meta,
                            skip_state_save,
                            logger)
                        if r['return'] > 0:
                            return r
                elif isinstance(exp[key], dict):
                    return {
                        'return': 1, 'error': 'Dictionary inputs are not supported for mlc experiment script'}
                else:
                    ii[key] = exp[key]
                    r = run_script_and_tag_experiment(
                        ii,
                        self_module.action_object,
                        experiment_action,
                        tags,
                        extra_exp_tags,
                        meta,
                        skip_state_save,
                        logger)
                    if r['return'] > 0:
                        return r

    return {'return': 0}


def run_script_and_tag_experiment(
        ii, script_action, experiment_action, tags, extra_exp_tags, script_meta, skip_state_save, logger):

    current_path = os.path.abspath(os.getcwd())
    experiment_meta = {}
    recursion_spaces = ''
    exp_tags = tags + extra_exp_tags
    ii = {'action': 'update',
          'target': 'experiment',
          'script_alias': script_meta['alias'],
          'script_uid': script_meta['uid'],
          'tags': ','.join(exp_tags),
          'extra_tags': ",".join(extra_exp_tags),
          'meta': experiment_meta,
          'force': True}

    r = experiment_action.access(ii)
    if r['return'] > 0:
        return r

    experiment = r['list'][0]

    logger.debug(
        recursion_spaces +
        '  - Changing to {}'.format(experiment.path))

    os.chdir(experiment.path)
    # Get current datetime in YYYY-MM-DD_HH-MM-SS format
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Create a folder name using the timestamp
    folder_name = f"run_{timestamp}"

    # Create the directory
    os.makedirs(folder_name, exist_ok=True)
    os.chdir(folder_name)

    if not skip_state_save:
        ssi = {'action': 'run',
               'target': 'script',
               'tags': 'save,system,state',
               'outfile': 'system_state_before.json',
               'quiet': True
               }
        r = script_action.access(ssi)
        if r['return'] > 0:
            return r

    start_time = time.time()
    r = script_action.access(ii)
    if r['return'] > 0:
        return r

    end_time = time.time()
    elapsed = end_time - start_time
    time_taken_string = format_elapsed(elapsed)
    logger.info(f"Time taken: {time_taken_string}")

    if not skip_state_save:
        ssi['outfile'] = 'system_state_after.json'
        r = script_action.access(ssi)
        if r['return'] > 0:
            return r

    '''
    exp_tags = tags
    ii = {'action': 'update',
          'target': 'experiment',
          'uid': experiment.meta['uid'],
          'meta': experiment.meta,
          'script_alias': meta['alias'],
          'replace_lists': True,  # To replace tags
          'tags': ','.join(exp_tags)}

    r = experiment_action.access(ii)
    if r['return'] > 0:
        return r
   '''
    os.chdir(current_path)
    logger.info(
        f"Experiment entry saved at: {os.path.join(experiment.path, folder_name)}")

    return {'return': 0, 'experiment': experiment, 'folder_name': folder_name}


def format_elapsed(seconds):
    if seconds < 60:
        return f"{seconds:.3f} seconds"
    elif seconds < 3600:
        mins, secs = divmod(seconds, 60)
        return f"{int(mins)} minutes {secs:.1f} seconds"
    else:
        hours, remainder = divmod(seconds, 3600)
        mins, secs = divmod(remainder, 60)
        return f"{int(hours)} hours {int(mins)} minutes {secs:.1f} seconds"


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
