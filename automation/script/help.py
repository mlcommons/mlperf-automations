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

    r = self_module._select_script(input_params)
    if r['return'] > 0:
        return r

    script = r['script']

    if not script:

        print("")
        print("Please use script tags or alias/uid to get help for a specific script")
        print("")
        print("Generic Inputs for all Scripts:")
        print("")
        print_input_descriptions(generic_inputs)

    else:
        metadata = script.meta
        script_path = script.path
        print_script_help(
            metadata,
            script_path,
            generic_inputs,
            env,
            self_module)

    return {'return': 0}


def print_script_help(metadata, script_path, generic_inputs, env, self_module):
    print("")
    print(f"Script Name: {metadata.get('alias', metadata['uid'])}")
    print(f"Tags: {', '.join(metadata.get('tags', []))}")
    # Print the run commands
    print_run_commands(metadata)

    input_mapping = metadata.get('input_mapping', {})
    input_description = metadata.get('input_description', {})
    default_env = metadata.get('default_env', {})

    print("")
    print("=" * 60)
    script_name = metadata.get('alias', metadata['uid'])
    print(f"  INPUTS FOR '{script_name}'")
    print("=" * 60)
    print("")

    if input_mapping:
        print_input_details(input_mapping, input_description, default_env)
    else:
        print(f"    No inputs defined for '{script_name}'.")

    variations = metadata.get('variations', {})

    if variations:
        print_variations_help(variations)
    else:
        print("    - No variations.")

    print("\n" + "=" * 60)
    print("  SCRIPT FILE PATHS")
    print("=" * 60)
    print("")

    print(
        f"""    Script meta file path: {os.path.join(script_path, "meta.yaml")}""")
    customize_path = os.path.join(script_path, "customize.py")
    if os.path.exists(customize_path):
        print(f"""    Script customize file path: {customize_path}""")
    else:
        print(
            f"""    Script customize file can be created at: {customize_path}""")

    run_script_name = self_module._get_script_name(env, script_path)
    run_script_path = os.path.join(script_path, run_script_name)
    if os.path.exists(run_script_path):
        print(f"""    Script run file path: {run_script_path}""")

    print("\n" + "=" * 60)
    print("  GENERIC INPUTS (common to all scripts)")
    print("=" * 60)
    print("")
    print("    To see all generic script inputs, run:")
    print("      $ mlc run script --help")
    print("")


def print_input_details(input_mapping, input_description, default_env):

    for i in input_mapping:
        if i not in input_description or input_description[i].get(
                'env', '') != input_mapping[i]:
            if i not in input_description:
                input_description[i] = {}
            input_description[i]['env_key'] = input_mapping[i]

    keys_to_delete = [
        key for key in input_description if key not in input_mapping and "." not in key]
    for key in keys_to_delete:
        del input_description[key]

    main_inputs = {}
    alias_inputs = {}

    if input_description:
        reverse_map = defaultdict(list)
        for k, v in input_mapping.items():
            reverse_map[v].append(k)

        for i in input_description:
            if i in input_mapping and input_mapping[i] in default_env:
                input_description[i]['default'] = default_env[input_mapping[i]]

        # Identify aliases
        for mapped_env, keys in reverse_map.items():
            if len(keys) > 1:
                canonical = keys[0]
                for alias in keys[1:]:
                    if alias in input_description:
                        input_description[alias] = {}
                        input_description[alias]['alias'] = canonical
                        input_description[alias]['desc'] = f"Alias for --{canonical}"
                        input_description[alias]['env_key'] = mapped_env

        # Separate main inputs from aliases
        for key, field in input_description.items():
            if field.get('alias'):
                alias_inputs[key] = field
            else:
                main_inputs[key] = field

    print_input_table(main_inputs)

    if alias_inputs:
        print("")
        print("    Aliases:")
        print("")
        _print_alias_table(alias_inputs)

    return


def _print_alias_table(alias_inputs):
    """Print aliases in a compact grouped format."""
    rows = []
    for key in sorted(alias_inputs):
        field = alias_inputs[key]
        canonical = field.get('alias', '')
        env_key = field.get('env_key', '')
        rows.append((f"--{key}", f"--{canonical}", env_key))

    flag_w = max(len(r[0]) for r in rows) + 2
    target_w = max(len(r[1]) for r in rows) + 2

    for flag, target, env_key in rows:
        print(
            f"    {flag.ljust(flag_w)}\u2192 {target.ljust(target_w)}({env_key})")


def _wrap_text(text, width, indent):
    """Wrap text to width with indent on continuation lines."""
    import textwrap
    lines = textwrap.wrap(text, width=width)
    if not lines:
        return ""
    return lines[0] + "".join(f"\n{indent}{l}" for l in lines[1:])


def print_input_table(input_descriptions):
    """Print inputs in a simple readable format."""
    if not input_descriptions:
        print("    No inputs")
        return

    # Compute alignment: all "or" keywords line up
    keys = sorted(input_descriptions)
    flag_w = max(len(f"--{k}") for k in keys) + 2

    detail_prefix = "        \u2514\u2500 "
    detail_indent = "           "
    wrap_width = 80

    for key in keys:
        field = input_descriptions[key]
        env_key = field.get('env_key', f"MLC_TMP_{key.upper()}")
        desc = field.get('desc', '')
        default = str(field['default']) if field.get('default') else ''
        choices = field.get("choices", "")

        # Main line: --flag  <aligned>  or  --env.ENV_KEY
        flag = f"--{key}"
        print(f"    {flag.ljust(flag_w)}or --env.{env_key}")

        # Detail lines for default, choices, description on separate lines
        if default:
            print(f"{detail_prefix}Default: {default}")
        if choices:
            detail_text = f"Choices: {choices}"
            wrapped = _wrap_text(detail_text, wrap_width, detail_indent)
            print(f"{detail_prefix}{wrapped}")
        if desc:
            wrapped = _wrap_text(desc, wrap_width, detail_indent)
            print(f"{detail_prefix}{wrapped}")

        print("")  # Blank line between entries

    return


def print_input_descriptions(input_descriptions):
    print_input_table(input_descriptions)


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
            output += f" [base: {base_str}]"

        if group != "ungrouped" and main_variations[var].get("default", False):
            output += " [Default]"

        grouped_output[group].append(output)

    # Console output structure
    print("")
    print("=" * 60)
    print("  VARIATIONS")
    print("=" * 60)
    print("")
    print("    Use variations by adding them with a _ prefix to the script tags.")
    print("    Example: mlcr <tags>,_<variation_name>")
    print("")

    for group in sorted(grouped_output):
        if group == "ungrouped":
            print(f"    {group.capitalize()} Variations:")
        else:
            print(
                f"    {group.capitalize()} Variations (only one can be selected at a time):")
        for line in grouped_output[group]:
            print(f"        - {line}")
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
