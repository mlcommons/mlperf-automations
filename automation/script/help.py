import os
from mlc import utils
from utils import *
import os
from collections import defaultdict


def display_help(self_module, input_params):
    """
    Generates the documentation of MLC scripts.

    Args:
        self_module: Reference to the current module for internal calls.
        input_params: Dictionary containing input parameters.

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

    # Step 2: Search for scripts
    search_result = self_module.search(input_params.copy())
    if search_result['return'] > 0:
        return search_result

    scripts_list = search_result['list']
    if not scripts_list:
        return {'return': 1, 'error': 'No scripts were found'}

    generic_inputs = self_module.input_flags_converted_to_env

    # Step 4: Iterate over scripts and generate help output
    for script in sorted(scripts_list, key=lambda x: x.meta.get('alias', '')):
        metadata = script.meta
        print_script_help(metadata, generic_inputs)

    return {'return': 0}


def print_script_help(metadata, generic_inputs):
    print("")
    print(f"Script Name: {metadata.get('alias', metadata['uid'])}")
    print(f"Tags: {', '.join(metadata.get('tags', []))}")
    # Print the run commands
    print_run_commands(metadata)
    print("")
    print("Script Inputs:")
    print("")

    input_mapping = metadata.get('input_mapping', {})
    input_description = metadata.get('input_description', {})
    default_env = metadata.get('default_env', {})

    print_input_details(input_mapping, input_description, default_env)

    print("")
    print("Generic Inputs for all Scripts:")
    print("")
    print_input_descriptions(generic_inputs)

    variations = metadata.get('variations', {})

    if variations:
        print_variations_help(variations)
    else:
        print("    - No variations.")

    print("\n" + "=" * 40 + "\n")  # Separator for clarity


def print_input_details(input_mapping, input_description, default_env):

    for i in input_mapping:
        if i not in input_description or input_description[i].get(
                'env', '') != input_mapping[i]:
            if i not in input_description:
                input_description[i] = {}
            input_description[i]['env_key'] = input_mapping[i]

    if input_description:
        reverse_map = defaultdict(list)
        for k, v in input_mapping.items():
            reverse_map[v].append(k)

        for i in input_description:
            if i in input_mapping and input_mapping[i] in default_env:
                input_description[i]['default'] = default_env[input_mapping[i]]

        # Add alias entries
        for mapped_env, keys in reverse_map.items():
            if len(keys) > 1:
                canonical = keys[0]
                for alias in keys[1:]:
                    if alias in input_description:
                        input_description[alias] = {}
                        input_description[alias]['alias'] = canonical
                        input_description[alias]['desc'] = f"""Alias for {canonical}"""

    print_input_descriptions(input_description)

    return


def print_input_descriptions(input_descriptions):
    for key in input_descriptions:
        env_key = input_descriptions.get(key, {}).get(
            'env_key', f"""MLC_TMP_{key.upper()}""")
        desc = input_descriptions.get(
            key, {}).get(
            'desc', 'No description available')
        default = input_descriptions.get(key, {}).get('default', 'None')
        # Use .ljust(15) to ensure the key occupies 15 characters minimum
        print(
            f"    --{key.ljust(26)} : maps to --env.{env_key}\n{' '.ljust(35)}{desc}\n{' '.ljust(35)}Default: {default}\n")


def print_variations_help(variations):
    # Data structures
    aliases = {}
    alias_reverse = defaultdict(list)
    bases = defaultdict(list)
    variation_groups = {}
    main_variations = {}

    # First pass: classify and build maps
    for name, attrs in variations.items():
        if "," in name:
            continue  # Skip composite variations
        if not isinstance(attrs, dict):
            main_variations[name] = {}
            continue
        if "alias" in attrs:
            aliases[name] = attrs["alias"]
            alias_reverse[attrs["alias"]].append(name)
        else:
            main_variations[name] = attrs
            # Group
            group = attrs.get("group", "ungrouped")
            if isinstance(group, list):
                group = group[0] if group else "ungrouped"
            variation_groups[name] = group
            # Base
            base = attrs.get("base", [])
            if isinstance(base, str):
                base = [base]
            bases[name] = base

    # Build grouped output in a simpler format
    grouped_output = defaultdict(list)

    for var in sorted(main_variations.keys()):
        group = variation_groups.get(var, "ungrouped")
        output = f"{var}"

        if var.endswith(".#"):
            output += " (dynamic substitution allowed)"

        if alias_reverse.get(var):
            alias_str = ", ".join(sorted(alias_reverse[var]))
            output += f" [Alias: {alias_str}]"

        if bases.get(var):
            base_str = ", ".join(bases[var])
            output += f" [Base: {base_str}]"

        if group != "ungrouped" and main_variations[var].get("default", False):
            output += " [Default]"

        grouped_output[group].append(output)

    # Console output structure
    print("\nVariations:\n")
    for group in sorted(grouped_output):
        print(f"\t{group.capitalize()} Variations:")
        for line in grouped_output[group]:
            print(f"\t    - {line}")
        print("")  # Blank line between groups


def print_run_commands(metadata):
    tags = ','.join(metadata.get('tags', []))
    input_mapping = metadata.get('input_mapping', {})

    # Build the command using the extracted tags
    command = f"mlcr {tags}"
    print("\nRun Commands:\n")
    print(f"    $ {command}")

    print("")
    print(f"""
        * Any input can be appended to the run command directly or using its --env.key mapping.
        * --env.key is useful to modify the input of a dependent script for which direct input may not be there in the main script.
        * Any variation can be selected by adding it to the tags using the _ prefix.
          For example, mlcr get,generic-python-lib,_panda turns on the panda variation for the get-generic-python-lib script.
        * --adr.<dep_name> can be used to modify the dependency(ies) with the name dep_name.
          For example, --adr.compiler.tags=gcc adds the tag 'gcc' to any dependency with the name compiler.
    """)


def infer_type(field):
    if "dtype" in field:
        return field["dtype"]
    elif "default" in field:
        return type(field["default"]).__name__
    else:
        return "str"
