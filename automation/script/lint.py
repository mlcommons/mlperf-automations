import os
import yaml
import copy
from mlc import utils
from utils import *

def lint_meta(self_module, input_params):
    """
    Lints MLC script metadata files by fixing key order and validating structure.

    Args:
        self_module: Reference to the current module for internal calls.
        i: Dictionary containing input parameters.

    Returns:
        Dictionary with the result of the operation. Keys:
        - 'return': 0 on success, >0 on error.
        - 'error': Error message (if any).
    """

    # Extract and handle basic inputs
    quiet = input_params.get('quiet', False)
    logger = self_module.logger
    env = input_params.get('env', {})
    generic_inputs = self_module.input_flags_converted_to_env
    generic_inputs = dict(sorted(generic_inputs.items()))

    # Search for scripts
    search_result = self_module.search(input_params.copy())
    if search_result['return'] > 0:
        return search_result

    scripts_list = search_result['list']
    print(scripts_list)
    if not scripts_list:
        return {'return': 1, 'error': 'No scripts were found'}


    env = input_params.get('env', {})
    state_data = input_params.get('state', {})
    constant_vars = input_params.get('const', {})
    constant_state = input_params.get('const_state', {})
    tag_values = input_params.get('tags', '').split(",")
    variation_tags = [tag[1:] for tag in tag_values if tag.startswith("_")]

    # Iterate over scripts
    for script in sorted(scripts_list, key=lambda x: x.meta.get('alias', '')):
        metadata = script.meta
        script_directory = script.path
        script_tags = metadata.get("tags", [])
        script_alias = metadata.get('alias', '')
        script_uid = metadata.get('uid', '')
        script_input_mapping = metadata.get('input_mapping', {})
        script_input_description = metadata.get('input_description', {})
        script_repo = script.repo

        # Sort YAML keys 
        sort_result = sort_meta_yaml_file(script_directory, quiet)
        if sort_result['return'] > 0:
            if not quiet:
                logger.error(
                    f"Failed to sort YAML keys for {script_alias}: {sort_result.get('error', '')}")
        elif sort_result.get('modified', False):
            if not quiet:
                logger.info(f"Sorted YAML keys for {script_alias}")
        elif not sort_result.get('modified', False):
            if not quiet:
                logger.info(f"No input mapping or variations keys to be sorted for {script_alias}")
    
    return {'return': 0}

def sort_meta_yaml_file(script_directory, quiet=False):
    """
    Sort specific keys in the meta.yaml file and save it back to disk.

    Args:
        script_directory: Path to the script directory
        quiet: Whether to suppress output messages

    Returns:
        Dictionary with 'return' (0 on success, >0 on error), 'modified' (bool),
        and 'error' (if any)
    """

    try:
        # Find meta.yaml file
        meta_yaml_path = None
        for filename in ['meta.yaml', 'meta.yml']:
            potential_path = os.path.join(script_directory, filename)
            if os.path.exists(potential_path):
                meta_yaml_path = potential_path
                break

        if not meta_yaml_path:
            return {'return': 1, 'error': 'meta.yaml file not found',
                    'modified': False}

        # Read current YAML content
        with open(meta_yaml_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        if not isinstance(data, dict):
            return {
                'return': 1, 'error': 'YAML does not contain a dictionary', 'modified': False}

        # Store original for comparison
        original_data = copy.deepcopy(data)

        # Sort input_mapping alphabetically
        if 'input_mapping' in data and isinstance(data['input_mapping'], dict):
            data['input_mapping'] = dict(sorted(data['input_mapping'].items()))

        # Sort variations: with 'group' first, then without 'group'
        if 'variations' in data and isinstance(data['variations'], dict):
            variations = data['variations']

            # Separate variations with and without 'group' key
            with_group = []
            without_group = []

            for key, value in variations.items():
                if isinstance(value, dict) and 'group' in value:
                    with_group.append((key, value))
                else:
                    without_group.append((key, value))

            # Sort both lists alphabetically by key
            with_group.sort(key=lambda x: x[0])
            without_group.sort(key=lambda x: x[0])

            # Combine them: with_group first, then without_group
            sorted_variations = {}
            for key, value in with_group + without_group:
                sorted_variations[key] = value

            data['variations'] = sorted_variations

        # Check if anything changed (including order)
        original_yaml = yaml.dump(
            original_data,
            default_flow_style=False,
            sort_keys=False)
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)

        if original_yaml == new_yaml:
            return {'return': 0, 'modified': False}

        # Write the sorted YAML back to file
        with open(meta_yaml_path, 'w', encoding='utf-8') as file:
            yaml.dump(data, file, default_flow_style=False, sort_keys=False,
                      allow_unicode=True, width=1000, indent=2)

        if not quiet:
            print(f"Sorted YAML keys in {meta_yaml_path}")

        return {'return': 0, 'modified': True, 'sorted_data': data}

    except Exception as e:
        return {'return': 1, 'error': str(e), 'modified': False}