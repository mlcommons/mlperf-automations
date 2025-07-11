import os
from mlc import utils
from utils import *
import logging
from pathlib import PureWindowsPath, PurePosixPath
import copy
from collections import defaultdict, OrderedDict



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
        script_repo = script.repo

        # Sort YAML keys before generating documentation
        sort_result = sort_meta_yaml_file(script_directory, quiet)
        if sort_result['return'] > 0:
            if not quiet:
                logger.warning(
                    f"Failed to sort YAML keys for {script_alias}: {sort_result.get('error', '')}")
        elif sort_result.get('modified', False):
            if not quiet:
                logger.info(f"Sorted YAML keys for {script_alias}")

        print(sort_result)
        if sort_result['return'] == 0 and sort_result.get('modified', False):
            metadata = sort_result['sorted_data']
            print(metadata)

        r = generate_docs(
            script_repo,
            metadata,
            script_directory,
            generic_inputs)
        if r['return'] > 0:
            continue

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
            sorted_variations = OrderedDict()
            for key, value in with_group + without_group:
                sorted_variations[key] = value

            data['variations'] = sorted_variations

        # Check if anything changed
        if data == original_data:
            return {'return': 0, 'modified': False}

        # Write the sorted YAML back to file
        with open(meta_yaml_path, 'w', encoding='utf-8') as file:
            yaml.dump(data, file, default_flow_style=False, sort_keys=False,
                      allow_unicode=True, width=1000)

        if not quiet:
            print(f"Sorted YAML keys in {meta_yaml_path}")

        return {'return': 0, 'modified': True, 'sorted_data': data}

    except Exception as e:
        return {'return': 1, 'error': str(e), 'modified': False}


def get_setup_readme(script_repo):
    repo_alias = os.path.basename(script_repo.meta.get('alias'))
    repo_name = repo_alias
    if '@' in repo_name:
        repo_name = repo_name.split('@')[1]

    setup_readme = f"""`mlcflow` stores all local data under `$HOME/MLC` by default. So, if there is space constraint on the home directory and you have more space on say `/mnt/user`, you can do
```
mkdir /mnt/user/MLC
ln -s /mnt/user/MLC $HOME/MLC
```
You can also use the `ENV` variable `MLC_REPOS` to control this location but this will need a set after every system reboot.

## Setup

If you are not on a Python development environment please refer to the [official docs](https://docs.mlcommons.org/mlcflow/install/) for the installation.

```bash
python3 -m venv mlcflow
. mlcflow/bin/activate
pip install mlcflow
```

- Using a virtual environment is recommended (per `pip` best practices), but you may skip it or use `--break-system-packages` if needed.

### Pull {repo_name}

Once `mlcflow` is installed:

```bash
mlc pull repo {repo_alias} --pat=<Your Private Access Token>
```
- `--pat` or `--ssh` is only needed if the repo is PRIVATE
- If `--pat` is avoided, you'll be asked to enter the password where you can enter your Private Access Token
- `--ssh` option can be used instead of `--pat=<>` option if you prefer to use SSH for accessing the github repository.
"""
    return {'return': 0, 'setup_readme': setup_readme}


def generate_docs(script_repo, metadata, script_path, generic_inputs):
    script_name = metadata.get('alias', metadata['uid'])
    info_doc_exists = os.path.exists(os.path.join(script_path, 'info.md'))
    if info_doc_exists:
        readme_line = "Edit [info.md](info.md) to add custom contents."
    else:
        readme_line = "Add custom content in [info.md](info.md)."
    readme_prefix = f"""This README is automatically generated. {readme_line} Please follow the [script execution document](https://docs.mlcommons.org/mlcflow/targets/script/execution-flow/) to understand more about the MLC script execution.
"""
    doc_content = f"""# README for {script_name}
{readme_prefix}
"""

    r = get_setup_readme(script_repo)
    if r['return'] > 0:
        return r

    setup_readme = r['setup_readme']
    doc_content += setup_readme

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

    for k in script_input_mapping:
        if k not in script_input_description:
            script_input_description[k] = {}

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
            line += " _(# can be substituted dynamically)_"

        if alias_reverse.get(var):
            alias_str = ", ".join(sorted(alias_reverse[var]))
            line += f" (alias: {alias_str})"

        if bases.get(var):
            base_str = ", ".join(bases[var])
            line += f" (base: {base_str})"

        if group != "ungrouped":
            if main_variations[var].get("default", False):
                line += f" (default)"

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

    reverse_map = defaultdict(list)
    for k, v in input_mapping.items():
        reverse_map[v].append(k)

    if input_description:
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
