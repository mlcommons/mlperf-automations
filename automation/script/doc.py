import os
from mlc import utils
from utils import *
import logging
from pathlib import PureWindowsPath, PurePosixPath
import copy
from collections import defaultdict


def generate_doc(self_module, input_params):
    """
    Generates the documentation of MLC scripts.

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

    # Step 2: Search for scripts
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

    # Step 4: Iterate over scripts and generate Dockerfile
    for script in sorted(scripts_list, key=lambda x: x.meta.get('alias', '')):
        metadata = script.meta
        script_directory = script.path
        script_tags = metadata.get("tags", [])
        script_alias = metadata.get('alias', '')
        script_uid = metadata.get('uid', '')
        script_input_mapping = metadata.get('input_mapping', {})
        script_input_description = metadata.get('input_description', {})

        r = generate_docs(metadata, script_directory, generic_inputs)
        if r['return'] > 0:
            continue

    return {'return': 0}


def generate_docs(metadata, script_path, generic_inputs):
    script_name = metadata.get('alias', metadata['uid'])
    info_doc_exists = os.path.exists(os.path.join(script_path, 'info.md'))
    if info_doc_exists:
        readme_line = "Edit [info.txt](info.txt) to add custom contents."
    else:
        readme_line = "Add custom content in [info.txt](info.txt)."
    readme_prefix = f"""This README is automatically generated. {readme_line} Please follow the [script execution document](https://docs.mlcommons.org/mlcflow/targets/script/execution-flow/) to understand more about the MLC script execution.
"""
    doc_content = f"""# README for {script_name}
{readme_prefix}
"""

    readme_dir = script_path

    if not os.path.exists(readme_dir):
        os.makedirs(readme_dir)

    script_tags = metadata.get("tags", [])
    script_tags_help = metadata.get("tags_help", '')
    if not script_tags_help:
        tags_string = ",".join(script_tags)
    else:
        tags_string = script_tags_help

    script_input_mapping = metadata.get('input_mapping', {})
    script_default_env = metadata.get('default_env', {})
    script_input_description = metadata.get('input_description', {})
    script_variations = metadata.get('variations', {})
    default_version = metadata.get('default_version')

    r = get_run_readme(
        tags_string,
        script_input_mapping,
        script_input_description,
        script_default_env,
        generic_inputs)
    if r['return'] > 0:
        return r

    run_readme = r['run_readme']

    doc_content += run_readme

    r = get_variations_readme(script_variations)
    if r['return'] > 0:
        return r
    variations_readme = r['variations_readme']
    doc_content += variations_readme

    example_commands_file = os.path.join(script_path, 'example-commands.md')

    # Read the file content if it exists
    if os.path.exists(example_commands_file):
        with open(example_commands_file, "r") as f:
            commands_readme = f.read()
    else:
        commands_readme = ''

    # Append the content to doc_content
    doc_content += commands_readme

    readme_path = os.path.join(readme_dir, "README.md")
    with open(readme_path, "w") as f:
        f.write(doc_content)
    print(f"Readme generated at {readme_path}")

    return {'return': 0}


def get_variations_readme(variations):

    # Data structures
    aliases = {}                # alias name -> real target
    alias_reverse = defaultdict(list)  # real target -> [aliases]
    bases = defaultdict(list)   # variation -> list of base variations
    variation_groups = {}       # variation -> group
    main_variations = {}        # all actual variations to process

    # First pass: classify and build maps
    for name, attrs in variations.items():
        if "," in name:
            continue  # ⛔ Skip composite variations
        if not isinstance(attrs, dict):
            main_variations[name] = {}
            continue
        if "alias" in attrs:
            aliases[name] = attrs["alias"]
            alias_reverse[attrs["alias"]].append(name)
        else:
            main_variations[name] = attrs
            # group
            group = attrs.get("group", "ungrouped")
            if isinstance(group, list):
                group = group[0] if group else "ungrouped"
            variation_groups[name] = group
            # base
            base = attrs.get("base", [])
            if isinstance(base, str):
                base = [base]
            bases[name] = base

    # Build grouped markdown output
    grouped_output = defaultdict(list)

    for var in sorted(main_variations.keys()):
        group = variation_groups.get(var, "ungrouped")
        line = f"- `{var}`"

        if var.endswith(".#"):
            line += " _(dynamic)_"

        if alias_reverse.get(var):
            alias_str = ", ".join(sorted(alias_reverse[var]))
            line += f" (alias: {alias_str})"

        if bases.get(var):
            base_str = ", ".join(bases[var])
            line += f" (base: {base_str})"

        grouped_output[group].append(line)

    # Write Markdown
    md_lines = ["## Variations\n"]

    for group in sorted(grouped_output):
        md_lines.append(f"### {group.capitalize()}\n")
        md_lines.extend(grouped_output[group])
        md_lines.append("")  # blank line between groups

    return {'return': 0, 'variations_readme': "\n".join(md_lines)}


def get_run_readme(tags, input_mapping, input_description,
                   default_env, generic_inputs):
    run_readme = f"""## Run Commands

```bash
mlcr {tags}
```

"""

    if input_description:
        for i in input_description:
            if i in input_mapping and input_mapping[i] in default_env:
                input_description[i]['default'] = default_env[input_mapping[i]]

        input_description_string = generate_markdown(
            "Script Inputs", input_description)
    else:
        input_description_string = "No script specific inputs"

    run_readme += input_description_string

    generic_input_string = generate_markdown(
        "Generic Script Inputs", generic_inputs)

    run_readme += f"""
{generic_input_string}
"""

    return {'return': 0, 'run_readme': run_readme}


def infer_type(field):
    if "dtype" in field:
        return field["dtype"]
    elif "default" in field:
        return type(field["default"]).__name__
    else:
        return "str"


def generate_markdown(heading, input_dict):
    lines = [
        f"### {heading}\n",
        "| Name | Description | Choices | Default |",
        "|------|-------------|---------|------|"]
    for key in sorted(
            input_dict, key=lambda k: input_dict[k].get("sort", 9999)):
        field = input_dict[key]
        desc = field.get("desc", "")
        choices = field.get("choices", "")
        default = field.get("default", "")
        dtype = infer_type(field)
        lines.append(f"| `--{key}` | {desc} | {choices} | `{default}` |")
    return "\n".join(lines)
