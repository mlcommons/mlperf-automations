import os
import yaml
import copy
from mlc import utils
from utils import *
from script.meta_schema import validate_meta


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
                logger.info(
                    f"No input mapping or variations keys to be sorted for {script_alias}")

        # Validate meta against schema
        meta_errors, meta_warnings = validate_meta(metadata, script_directory)
        if meta_errors:
            for e in meta_errors:
                logger.error(f"[{script_alias}] {e}")
        if meta_warnings and not quiet:
            for w in meta_warnings:
                logger.warning(f"[{script_alias}] {w}")

    return {'return': 0}


# Canonical key order for top-level meta.yaml keys.
# Keys are grouped logically so readers can quickly find what they need.
# Keys not in this list are placed at the end in their original order.
TOP_LEVEL_KEY_ORDER = [
    # Identity
    "alias",
    "uid",
    "automation_alias",
    "automation_uid",

    # Metadata
    "name",
    "category",
    "category_sort",
    "developers",
    "tags",
    "tags_help",
    "private",
    "min_mlc_version",

    # Cache
    "cache",
    "can_force_cache",
    "cache_expiration",
    "extra_cache_tags_from_env",
    "clean_files",
    "clean_output_files",

    # Environment
    "default_env",
    "env",
    "new_env_keys",
    "new_state_keys",
    "local_env_keys",
    "file_path_env_keys",
    "folder_path_env_keys",
    "env_key_mappings",

    # Input
    "input_mapping",
    "input_description",

    # Dependencies
    "predeps",
    "deps",
    "prehook_deps",
    "posthook_deps",
    "post_deps",

    # Variations
    "default_variation",
    "default_variations",
    "variation_groups_order",
    "invalid_variation_combinations",
    "valid_variation_combinations",
    "variations",

    # Versions
    "default_version",
    "versions",

    # Conditional
    "update_meta_if_env",

    # Docker / container
    "docker",

    # Output / debugging
    "print_env_at_the_end",
    "print_files_if_script_error",
    "warnings",
    "sudo_install",
    "sort",
    "remote_run",

    # Tests
    "tests",
]


# Section groups: each entry is (header_comment, [keys_in_this_group]).
# A comment is inserted before the first key from each group that appears in the file.
SECTION_GROUPS = [
    # Identity keys (alias, uid, etc.) get no header - they're always first
    ("# Metadata",                ["name", "category", "category_sort", "developers", "tags", "tags_help", "private", "min_mlc_version"]),
    ("# Cache",                   ["cache", "can_force_cache", "cache_expiration", "extra_cache_tags_from_env", "clean_files", "clean_output_files"]),
    ("# Environment",             ["default_env", "env", "new_env_keys", "new_state_keys", "local_env_keys", "file_path_env_keys", "folder_path_env_keys", "env_key_mappings"]),
    ("# Input mapping",           ["input_mapping", "input_description"]),
    ("# Dependencies",            ["predeps", "deps", "prehook_deps", "posthook_deps", "post_deps"]),
    ("# Variations",              ["default_variation", "default_variations", "variation_groups_order", "invalid_variation_combinations", "valid_variation_combinations", "variations"]),
    ("# Versions",                ["default_version", "versions"]),
    ("# Conditional meta updates",["update_meta_if_env"]),
    ("# Docker / container",      ["docker"]),
    ("# Output / debugging",      ["print_env_at_the_end", "print_files_if_script_error", "warnings", "sudo_install", "sort", "remote_run"]),
    ("# Tests",                   ["tests"]),
]


def _build_key_to_header(data_keys):
    """Build a mapping from key -> header, only for the *first* key in each
    section group that actually appears in data_keys."""
    data_key_set = set(data_keys)
    key_to_header = {}
    for header, group_keys in SECTION_GROUPS:
        for k in group_keys:
            if k in data_key_set:
                key_to_header[k] = header
                break  # only tag the first present key per group
    return key_to_header


def insert_section_comments(yaml_string, data_keys):
    """Insert section header comments before the first key of each group.
    Only inserts a header once per section even if multiple keys from that
    section are present."""
    key_to_header = _build_key_to_header(data_keys)
    lines = yaml_string.split('\n')
    result = []

    for line in lines:
        # Check if this line is a top-level key (not indented, has a colon)
        if line and not line[0].isspace() and ':' in line:
            key = line.split(':')[0].strip()
            header = key_to_header.get(key)
            if header:
                # Add blank line before section (unless at the very start)
                if result and result[-1] != '':
                    result.append('')
                result.append(header)
        result.append(line)

    return '\n'.join(result)


def reorder_top_level_keys(data):
    """Reorder top-level keys in data dict according to TOP_LEVEL_KEY_ORDER.
    Keys not in the canonical list are appended at the end in original order."""
    ordered = {}
    for key in TOP_LEVEL_KEY_ORDER:
        if key in data:
            ordered[key] = data[key]
    # Append any remaining keys not in the canonical order
    for key in data:
        if key not in ordered:
            ordered[key] = data[key]
    return ordered


def sort_meta_yaml_file(script_directory, quiet=False):
    """
    Sort and reorder keys in the meta.yaml file and save it back to disk.

    Applies three transformations:
    1. Reorders top-level keys into a canonical, grouped order.
    2. Sorts input_mapping keys alphabetically.
    3. Sorts variations: grouped by group name first, then ungrouped alphabetically.

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

        # Store original raw text for comparison
        with open(meta_yaml_path, 'r', encoding='utf-8') as file:
            original_raw = file.read()
        original_data = copy.deepcopy(data)

        # 1. Reorder top-level keys
        data = reorder_top_level_keys(data)

        # 2. Sort input_mapping alphabetically
        if 'input_mapping' in data and isinstance(data['input_mapping'], dict):
            data['input_mapping'] = dict(sorted(data['input_mapping'].items()))

        # 3. Sort variations: grouped consecutively by group name, then ungrouped
        if 'variations' in data and isinstance(data['variations'], dict):
            variations = data['variations']

            # Separate variations by group
            with_group = []
            without_group = []

            for key, value in variations.items():
                if isinstance(value, dict) and 'group' in value:
                    group = value['group']
                    if isinstance(group, list):
                        group = group[0] if group else ''
                    with_group.append((key, value, group))
                else:
                    without_group.append((key, value))

            # Sort grouped variations by (group_name, variation_name)
            # so variations within the same group are consecutive
            with_group.sort(key=lambda x: (x[2], x[0]))
            without_group.sort(key=lambda x: x[0])

            # Combine: grouped first (consecutive by group), then ungrouped
            sorted_variations = {}
            for key, value, _ in with_group:
                sorted_variations[key] = value
            for key, value in without_group:
                sorted_variations[key] = value

            data['variations'] = sorted_variations

        # Generate new output and check if anything changed
        new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False,
                             allow_unicode=True, width=1000, indent=2)
        new_yaml = insert_section_comments(new_yaml, list(data.keys()))

        if original_raw.rstrip() == new_yaml.rstrip():
            return {'return': 0, 'modified': False}

        # Write the sorted YAML back to file with section comments
        yaml_output = yaml.dump(data, default_flow_style=False, sort_keys=False,
                                allow_unicode=True, width=1000, indent=2)
        yaml_output = insert_section_comments(yaml_output, list(data.keys()))
        with open(meta_yaml_path, 'w', encoding='utf-8') as file:
            file.write(yaml_output)

        if not quiet:
            print(f"Sorted YAML keys in {meta_yaml_path}")

        return {'return': 0, 'modified': True, 'sorted_data': data}

    except Exception as e:
        return {'return': 1, 'error': str(e), 'modified': False}
