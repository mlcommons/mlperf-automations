import os
from mlc import utils
from utils import *
import logging
from script.docker_utils import regenerate_script_cmd
import copy


def apptainerfile(self_module, input_params):

    # Step 1: Prune and prepare input
    prune_result = prune_input(
        {'input': input_params, 'extra_keys_starts_with': ['apptainer_']})
    if prune_result['return'] > 0:
        return prune_result

    logger = self_module.logger

    run_command_arc = prune_result['new_input']
    current_directory = os.getcwd()
    is_quiet_mode = input_params.get('quiet', False)

    # Step 2: Process Apptainer-related configurations
    env = input_params.get('env', {})
    state_data = input_params.get('state', {})
    constant_vars = input_params.get('const', {})
    constant_state = input_params.get('const_state', {})
    tag_values = input_params.get('tags', '').split(",")
    variation_tags = [tag[1:] for tag in tag_values if tag.startswith("_")]

    if is_quiet_mode:
        env['MLC_QUIET'] = 'yes'

    r = self_module._select_script(input_params)
    if r['return'] > 0:
        return r

    script = r['script']

    if not script:
        return {'return': 1,
                'error': 'No scripts were found for generating apptainer definition file'}

    metadata = script.meta
    script_directory = script.path
    script_tags = metadata.get("tags", [])
    script_alias = metadata.get('alias', '')
    script_uid = metadata.get('uid', '')

    if not hasattr(self_module, 'run_state'):
        self_module.run_state = self_module.init_run_state(
            input_params.get('run_state'))

    r = self_module.update_run_state_for_selected_script_and_variations(
        script, input_params)

    run_state = self_module.run_state

    apptainer_settings = run_state.get('docker', {})
    apptainer_settings_default_env = apptainer_settings.get('default_env', {})
    for key in apptainer_settings_default_env:
        env.setdefault(key, apptainer_settings_default_env[key])

    if not apptainer_settings.get('run', True) and not input_params.get(
            'apptainer_run_override', False):
        logger.info("Apptainer 'run' is set to False in meta.yaml")
        return {'return': 0, 'warning': 'Apptainer run is set to false in script meta'}

    # Handle build dependencies
    show_time = input_params.get('show_time', False)
    deps = apptainer_settings.get('build_deps', [])
    if deps:
        r = self_module._run_deps(
            deps, [], '', '', False, '',
            show_time, ' ', run_state)
        if r['return'] > 0:
            return r

    # For update_meta_if_env to work
    update_state_result = self_module.update_state_from_meta(
        metadata,
        run_state=run_state,
        i=input_params
    )
    if update_state_result['return'] > 0:
        return update_state_result

    apptainer_settings = run_state.get('docker', {})

    # Prune temporary environment variables
    run_command = copy.deepcopy(run_command_arc)
    for key in list(run_command.get('env', {}).keys()):
        if key.startswith("MLC_TMP_"):
            del run_command['env'][key]

    # Regenerate script command
    regenerate_result = regenerate_script_cmd({
        'script_uid': script_uid,
        'script_alias': script_alias,
        'run_cmd': run_command,
        'tags': script_tags,
        'fake_run': True,
        'docker_settings': apptainer_settings,
        'docker_run_cmd_prefix': input_params.get('apptainer_run_cmd_prefix', apptainer_settings.get('run_cmd_prefix', ''))
    })
    if regenerate_result['return'] > 0:
        return regenerate_result

    run_command_string = regenerate_result['run_cmd_string']

    # Prepare Apptainer-specific inputs
    apptainer_inputs, def_file_path = prepare_apptainer_inputs(
        input_params, apptainer_settings, script, False, self_module.action_object)

    # Handle optional dependencies and comments
    if input_params.get('print_deps'):
        mlc_input = {
            'action': 'run', 'automation': 'script', 'tags': input_params.get('tags'),
            'print_deps': True, 'quiet': True, 'silent': True,
            'fake_run': True, 'fake_deps': True
        }
        deps_result = self_module.action_object.access(mlc_input)
        if deps_result['return'] > 0:
            return deps_result
        comments = [
            f"# {dep}" for dep in deps_result['new_state']['print_deps']]
    else:
        comments = []

    apptainer_env = apptainer_inputs.get('env')
    if apptainer_env:
        apptainer_env = apptainer_env.copy()
    else:
        apptainer_env = {}

    apptainer_env['MLC_RUN_STATE_DOCKER'] = True
    state = {}
    state['dockerfile_env'] = apptainer_env

    # Generate Apptainer definition file
    mlc_apptainer_input = {
        'action': 'run', 'automation': 'script', 'tags': 'build,apptainerfile',
        'fake_run_option': " " if apptainer_inputs.get('real_run') else " --fake_run",
        'comments': comments, 'run_cmd': f"{run_command_string} --quiet",
        'script_tags': input_params.get('tags'),
        'env': env,
        'state': state,
        'quiet': True, 'real_run': True
    }

    if apptainer_inputs.get('mlc_repo_path', '') != '':
        mlc_apptainer_input['mlc_repo_path'] = apptainer_inputs['mlc_repo_path']

    apptainer_v = False
    apptainer_s = False
    if is_true(input_params.get(
            'apptainer_v', input_params.get('apptainer_verbose', False))):
        apptainer_v = True
    if is_true(input_params.get(
            'apptainer_s', input_params.get('apptainer_silent', False))):
        apptainer_s = True

    if apptainer_s and apptainer_v:
        logger.warning(
            "Both verbose and silent is set to True. Verbose will take precedence.")
        apptainer_s = False

    if not apptainer_s and not apptainer_v:
        if logger.level == logging.DEBUG:
            apptainer_v = True
        elif logger.level == logging.WARNING:
            apptainer_s = True

    if apptainer_s:
        mlc_apptainer_input['run_cmd'] += ' -s'
    elif apptainer_v:
        mlc_apptainer_input['run_cmd'] += ' -v'

    mlc_apptainer_input.update(apptainer_inputs)

    deffile_result = self_module.action_object.run(mlc_apptainer_input)
    if deffile_result['return'] > 0:
        return deffile_result

    logger.info(f"Apptainer definition file generated at {def_file_path}")

    return {'return': 0}


def apptainer_run(self_module, i):
    """
    Automates the execution of MLC scripts within an Apptainer container.

    Args:
        self_module: Reference to the current module for internal calls.
        i: Dictionary containing input parameters for the Apptainer execution.

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

    self_module.env = env

    if quiet:
        env['MLC_QUIET'] = 'yes'

    regenerate_def_file = not i.get('apptainer_noregenerate', False)
    rebuild_apptainer_image = i.get('apptainer_rebuild', False)

    # Prune unnecessary Apptainer-related input keys
    r = prune_input({'input': i, 'extra_keys_starts_with': ['apptainer_']})
    f_run_cmd = r['new_input']

    # Save current directory and prepare to search for scripts
    cur_dir = os.getcwd()

    env['MLC_RUN_STATE_DOCKER'] = False
    self_module.state, self_module.const, self_module.const_state = i.get(
        'state', {}), i.get(
        'const', {}), i.get(
        'const_state', {})

    state = self_module.state
    const = self_module.const
    const_state = self_module.const_state

    variation_tags = [t[1:]
                      for t in i.get('tags', '').split(",") if t.startswith("_")]

    add_deps_recursive = i.get('add_deps_recursive', {})

    input_i = copy.deepcopy(i)

    r = self_module._select_script(i)
    if r['return'] > 0:
        return r

    script = r['script']

    if not script:
        return {'return': 1,
                'error': 'No scripts were found for generating apptainer definition file'}

    meta, script_path = script.meta, script.path
    tags, script_alias, script_uid = meta.get(
        "tags", []), meta.get(
        'alias', ''), meta.get(
        'uid', '')

    mounts = copy.deepcopy(
        i.get(
            'apptainer_mounts',
            []))
    variations = meta.get('variations', {})

    if not hasattr(self_module, 'run_state'):
        self_module.run_state = self_module.init_run_state(
            i.get('run_state'))

    r = self_module.update_run_state_for_selected_script_and_variations(
        script, i)
    if r['return'] > 0:
        return r

    run_state = self_module.run_state

    apptainer_settings = run_state.get('docker', {})

    apptainer_settings_default_env = apptainer_settings.get('default_env', {})
    for key in apptainer_settings_default_env:
        env.setdefault(key, apptainer_settings_default_env[key])

    deps = apptainer_settings.get('deps', [])
    if deps:
        r = self_module._run_deps(
            deps, [], '', '', False, '',
            show_time, ' ', run_state)
        if r['return'] > 0:
            return r

    # For updating meta from update_meta_if_env
    r = self_module.update_state_from_meta(
        meta,
        run_state=run_state,
        i=i)
    if r['return'] > 0:
        return r

    # Skip scripts marked as non-runnable
    if not apptainer_settings.get('run', True) and not i.get(
            'apptainer_run_override', False):
        logger.info("apptainer.run set to False in meta.yaml")
        return {'return': 0, 'warning': 'Apptainer run is set to false in script meta'}

    # Regenerate definition file if required
    if regenerate_def_file:
        r = apptainerfile(self_module, input_i)
        if r['return'] > 0:
            return r

    # Ensure Apptainer is available
    r = self_module.action_object.access(
        {'action': 'run', 'automation': 'script', 'tags': "get-apptainer", 'quiet': True})
    if r['return'] > 0:
        return r

    r = self_module._update_env_from_input(env, i)
    if r['return'] > 0:
        return r

    # Prepare Apptainer-specific inputs
    apptainer_inputs, def_file_path = prepare_apptainer_inputs(
        i, apptainer_settings, script, True, self_module.action_object)

    if apptainer_inputs is None:
        return {'return': 1, 'error': 'Error preparing Apptainer inputs'}

    apptainer_input_mapping = apptainer_settings.get('input_mapping')

    # Update env based on apptainer_input_mapping if they are in input
    if apptainer_input_mapping and i:
        env.update({apptainer_input_mapping[key]: i[key]
                    for key in apptainer_input_mapping if key in i})

    # Handle bind mounts from environment variables
    bind_mounts = process_apptainer_mounts(mounts, env, apptainer_settings, run_state)
    container_env_string = bind_mounts.get('container_env_string', '')

    # Generate the run command
    r = regenerate_script_cmd({'script_uid': script_uid,
                               'script_alias': script_alias,
                               'tags': tags,
                               'run_cmd': f_run_cmd})
    if r['return'] > 0:
        return r
    final_run_cmd = f"""{r['run_cmd_string']} {container_env_string} """

    # Execute the Apptainer container
    mlc_apptainer_input = {
        'action': 'run', 'target': 'script', 'tags': 'run,apptainer,container',
        'rebuild': rebuild_apptainer_image,
        'env': env,
        'script_tags': i.get('tags'), 'run_cmd': final_run_cmd,
        'quiet': True, 'real_run': True,
        'add_deps_recursive': {'build-apptainer-image': {'def_file': def_file_path}}
    }
    utils.merge_dicts({'dict1': mlc_apptainer_input,
                       'dict2': apptainer_inputs,
                       'append_lists': True,
                       'append_unique': True})

    r = self_module.action_object.access(mlc_apptainer_input)
    if r['return'] > 0:
        return r

    return {'return': 0}


def prepare_apptainer_inputs(input_params, apptainer_settings,
                             script, run_stage, mlc):
    """
    Prepares Apptainer-specific inputs such as definition file path and runtime options.

    Args:
        input_params: Input dictionary with user-specified overrides.
        apptainer_settings: Apptainer settings from the script's metadata (docker key).
        script: Script being executed.
        run_stage: Whether this is the run stage (vs build stage).
        mlc: MLC action object.

    Returns:
        Tuple with Apptainer inputs dictionary and definition file path.
    """
    import json

    keys = [
        "mlc_repo", "mlc_repo_branch", "base_image", "os", "os_version", "mlc_repo_path",
        "mlc_repos", "skip_mlc_sys_upgrade", "extra_sys_deps", "image_name",
        "gh_token", "fake_run_deps", "run_final_cmds", "real_run", "copy_files", "path", "env"
    ]

    if run_stage:
        keys += [
            "skip_run_cmd", "pre_run_cmds", "run_cmd_prefix",
            "nv", "rocm", "bind", "writable", "writable_tmpfs",
            "cleanenv", "fakeroot", "no_home", "contain", "containall",
            "overlay", "extra_args", "sandbox"
        ]

    # Collect inputs
    apptainer_inputs = {
        key: input_params.get(
            f"apptainer_{key}", apptainer_settings.get(
                key, get_apptainer_default(key)))
        for key in keys
        if (value := input_params.get(f"apptainer_{key}", apptainer_settings.get(key, get_apptainer_default(key)))) is not None
    }

    # Resolve default os_version from apptainerinfo.json if not specified
    if not apptainer_inputs.get('os_version', ''):
        try:
            build_deffile_scripts = mlc.access(
                {'action': 'search', 'target': 'script', 'tags': 'build,apptainerfile'})
            if build_deffile_scripts.get('list'):
                apptainerinfo_path = os.path.join(
                    build_deffile_scripts['list'][0].path, 'apptainerinfo.json')
                with open(apptainerinfo_path) as _f:
                    apptainerinfo = json.load(_f)
                distro_config = apptainerinfo.get(
                    'distros', {}).get(
                    apptainer_inputs.get(
                        'os', ''), {})
                apptainer_inputs['os_version'] = distro_config.get(
                    'default_version',
                    list(distro_config['versions'].keys())[-1] if distro_config.get('versions') else '')
        except Exception:
            pass

    # Determine definition file path
    apptainer_base_image = apptainer_inputs.get('base_image')
    apptainer_path = apptainer_inputs.get('path')
    if not apptainer_path:
        script_meta = script.meta
        script_uid = script_meta['uid']
        script_alias = script_meta.get('alias')
        folder_name = f"""{script_alias}_{script_uid[:5]}"""
        apptainer_path = os.path.join(
            mlc.repos_path, 'local', 'apptainer', folder_name)
    def_filename_suffix = (
        apptainer_base_image.replace('/', '-').replace(':', '-')
        if apptainer_base_image else f"{apptainer_inputs['os']}_{apptainer_inputs['os_version']}"
    )
    def_file_path = os.path.join(
        apptainer_path,
        'definitions',
        f"{def_filename_suffix}.def")

    apptainer_inputs['file_path'] = def_file_path

    return apptainer_inputs, def_file_path


def process_apptainer_mounts(mounts, env, apptainer_settings, run_state):
    """
    Processes bind mounts for Apptainer.

    Args:
        mounts: List of existing mount/bind configurations.
        env: Current environment variables dictionary.
        apptainer_settings: Apptainer settings from the script's metadata.
        run_state: Current run state.

    Returns:
        Dictionary with processed mounts and container env string.
    """
    import re

    if 'mounts' in apptainer_settings:
        mounts.extend(apptainer_settings['mounts'])

    container_env_string = ""

    for index in range(len(mounts)):
        mount = mounts[index]

        # Resolve any environment variable placeholders
        placeholders = re.findall(r'\${{ (.*?) }}', mount)
        for placeholder in placeholders:
            if placeholder in env and isinstance(env[placeholder], str):
                mount = mount.replace(f"${{{{ {placeholder} }}}}", env[placeholder])
            else:
                mounts[index] = None
                break

        if mounts[index] is not None:
            mounts[index] = mount

    # Remove invalid mounts
    mounts = [item for item in mounts if item is not None]

    return {'return': 0, 'mounts': mounts,
            'container_env_string': container_env_string}


def get_apptainer_default(key):
    defaults = {
        "mlc_repo": "mlcommons@mlperf-automations",
        "mlc_repo_branch": "dev",
        "os": "ubuntu",
        "os_version": "",
        "fake_run_deps": False,
        "run_final_cmds": [],
        "skip_run_cmd": False,
        "pre_run_cmds": [],
        "run_cmd_prefix": '',
        "writable_tmpfs": True,
        "cleanenv": True,
    }
    if key in defaults:
        return defaults[key]
    return None
