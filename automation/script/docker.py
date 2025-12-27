import os
from mlc import utils
from utils import *
import logging
from pathlib import PureWindowsPath, PurePosixPath
from script.docker_utils import *
import copy


def dockerfile(self_module, input_params):

    # Step 1: Prune and prepare input
    prune_result = prune_input(
        {'input': input_params, 'extra_keys_starts_with': ['docker_']})
    if prune_result['return'] > 0:
        return prune_result

    logger = self_module.logger

    run_command_arc = prune_result['new_input']
    current_directory = os.getcwd()
    is_quiet_mode = input_params.get('quiet', False)
    is_console_output = input_params.get('out') == 'con'

    # Step 2: Process Dockerfile-related configurations
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
                'error': 'No scripts were found for generating dockerfile'}

    metadata = script.meta
    script_directory = script.path
    script_tags = metadata.get("tags", [])
    script_alias = metadata.get('alias', '')
    script_uid = metadata.get('uid', '')

    run_state = {
        'deps': [],
        'fake_deps': [],
        'parent': None,
        'script_id': f"{script_alias},{script_uid}",
        'script_variation_tags': variation_tags
    }

    docker_settings = metadata.get('docker', {})
    docker_settings_default_env = docker_settings.get('default_env', {})
    for key in docker_settings_default_env:
        env.setdefault(key, docker_settings_default_env[key])

    state_data['docker'] = docker_settings
    add_deps_recursive = input_params.get('add_deps_recursive', {})

    self_module.env = env
    self_module.state = state_data
    self_module.const = constant_vars
    self_module.const_state = constant_state

    # Update state with metadata and variations
    update_state_result = self_module.update_state_from_meta(
        metadata,
        deps=[],
        post_deps=[],
        prehook_deps=[],
        posthook_deps=[],
        new_env_keys=[],
        new_state_keys=[],
        run_state=run_state,
        i=input_params
    )
    if update_state_result['return'] > 0:
        return update_state_result

    update_variations_result = self_module._update_state_from_variations(
        input_params, metadata, variation_tags, metadata.get(
            'variations', {}),
        deps=[],  # Add your dependencies if needed
        post_deps=[],  # Add post dependencies if needed
        prehook_deps=[],  # Add prehook dependencies if needed
        posthook_deps=[],  # Add posthook dependencies if needed
        new_env_keys_from_meta=[],  # Add keys from meta if needed
        new_state_keys_from_meta=[],  # Add state keys from meta if needed
        run_state=run_state,
        recursion_spaces=''
    )
    if update_variations_result['return'] > 0:
        return update_variations_result

    # Set Docker-specific configurations
    docker_settings = state_data['docker']

    if is_true(docker_settings.get('pass_docker_to_script', False)):
        input_params['docker'] = True
        r = self_module.run(input_params)
        return r

    if not docker_settings.get('run', True) and not input_params.get(
            'docker_run_override', False):
        logger.info("Docker 'run' is set to False in meta.json")
        return {'return': 0, 'warning': 'Docker run is set to false in script meta'}

    # Handle build dependencies
    show_time = input_params.get('show_time', False)
    deps = docker_settings.get('build_deps', [])
    if deps:
        r = self_module._run_deps(
            deps, [], '', '', False, '',
            show_time, ' ', run_state)
        if r['return'] > 0:
            return r

    update_state_result = self_module.update_state_from_meta(
        metadata,
        deps=[],
        post_deps=[],
        prehook_deps=[],
        posthook_deps=[],
        new_env_keys=[],
        new_state_keys=[],
        run_state=run_state,
        i=input_params
    )
    if update_state_result['return'] > 0:
        return update_state_result
    docker_settings = state_data['docker']

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
        'docker_settings': docker_settings,
        'docker_run_cmd_prefix': input_params.get('docker_run_cmd_prefix', docker_settings.get('run_cmd_prefix', ''))
    })
    if regenerate_result['return'] > 0:
        return regenerate_result

    run_command_string = regenerate_result['run_cmd_string']

    # Prepare Docker-specific inputs
    docker_inputs, dockerfile_path = prepare_docker_inputs(
        input_params, docker_settings, script, False, self_module.action_object)

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
            f"#RUN {dep}" for dep in deps_result['new_state']['print_deps']]
    else:
        comments = []

    # Push Docker image if specified
    if str(input_params.get('docker_push_image')
           ).lower() in ['true', 'yes', '1']:
        env['MLC_DOCKER_PUSH_IMAGE'] = 'yes'

    dockerfile_env = docker_inputs.get('env', {})
    dockerfile_build_env = docker_inputs.get('build_env', {})

    dockerfile_env['MLC_RUN_STATE_DOCKER'] = True
    # Generate Dockerfile
    mlc_docker_input = {
        'action': 'run', 'automation': 'script', 'tags': 'build,dockerfile',
        'fake_run_option': " " if docker_inputs.get('real_run') else " --fake_run",
        'comments': comments, 'run_cmd': f"{run_command_string} --quiet",
        'script_tags': input_params.get('tags'), 'env': env,
        'dockerfile_env': dockerfile_env,
        'dockerfile_build_env': dockerfile_build_env,
        'quiet': True, 'real_run': True
    }

    if docker_inputs.get('mlc_repo_path', '') != '':
        mlc_docker_input['mlc_repo_path'] = docker_inputs['mlc_repo_path']

    docker_v = False
    docker_s = False
    if is_true(input_params.get(
            'docker_v', input_params.get('docker_verbose', False))):
        docker_v = True
    if is_true(input_params.get(
            'docker_s', input_params.get('docker_silent', False))):
        docker_s = True

    if docker_s and docker_v:
        logger.warning(
            "Both verbose and silent is set to True. Verbose will take precedence.")
        docker_s = False

    if not docker_s and not docker_v:
        if logger.level == logging.DEBUG:
            docker_v = True
        elif logger.level == logging.WARNING:
            docker_s = True

    if docker_s:
        mlc_docker_input['run_cmd'] += ' -s'
    elif docker_v:
        mlc_docker_input['run_cmd'] += ' -v'

    mlc_docker_input.update(docker_inputs)

    dockerfile_result = self_module.action_object.access(mlc_docker_input)
    if dockerfile_result['return'] > 0:
        return dockerfile_result

    logger.info(f"Dockerfile generated at {dockerfile_path}")

    return {'return': 0}


def docker_run(self_module, i):
    """
    Automates the execution of MLC scripts within a Docker container.

    Args:
        self_module: Reference to the current module for internal calls.
        i: Dictionary containing input parameters for the Docker execution.

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

    regenerate_docker_file = not i.get('docker_noregenerate', False)
    rebuild_docker_image = i.get('docker_rebuild', False)

    # Prune unnecessary Docker-related input keys
    r = prune_input({'input': i, 'extra_keys_starts_with': ['docker_']})
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

    docker_cache = i.get('docker_cache', "yes")
    if is_false(docker_cache):
        env.setdefault('MLC_DOCKER_CACHE', docker_cache)

    image_repo = i.get('docker_image_repo', '')
    add_deps_recursive = i.get('add_deps_recursive', {})

    input_i = copy.deepcopy(i)

    r = self_module._select_script(i)
    if r['return'] > 0:
        return r

    script = r['script']

    if not script:
        return {'return': 1,
                'error': 'No scripts were found for generating dockerfile'}

    meta, script_path = script.meta, script.path
    tags, script_alias, script_uid = meta.get(
        "tags", []), meta.get(
        'alias', ''), meta.get(
        'uid', '')

    mounts = copy.deepcopy(
        i.get(
            'docker_mounts',
            []))  # do we need a copy here?
    variations = meta.get('variations', {})

    # take the folder path as well as file path env variables from meta
    file_path_env_keys = meta.get('file_path_env_keys', [])
    folder_path_env_keys = meta.get('folder_path_env_keys', [])

    docker_settings = meta.get('docker', {})
    docker_settings_default_env = docker_settings.get('default_env', {})
    for key in docker_settings_default_env:
        env.setdefault(key, docker_settings_default_env[key])

    self_module.state['docker'] = docker_settings
    run_state = {
        'deps': [], 'fake_deps': [], 'parent': None,
        'script_id': f"{script_alias},{script_uid}",
        'script_variation_tags': variation_tags,
        'file_path_env_keys': file_path_env_keys,
        'folder_path_env_keys': folder_path_env_keys
    }

    # Update state and handle variations
    r = self_module.update_state_from_meta(meta, deps=[],
                                           post_deps=[],
                                           prehook_deps=[],
                                           posthook_deps=[],
                                           new_env_keys=[],
                                           new_state_keys=[], run_state=run_state, i=i)
    if r['return'] > 0:
        return r

    r = self_module._update_state_from_variations(
        i, meta, variation_tags, variations, deps=[],
        post_deps=[],
        prehook_deps=[],
        posthook_deps=[],
        new_env_keys_from_meta=[],
        new_state_keys_from_meta=[],
        run_state=run_state)
    if r['return'] > 0:
        return r

    docker_settings = self_module.state['docker']

    deps = docker_settings.get('deps', [])
    if deps:
        r = self_module._run_deps(
            deps, [], '', '', False, '',
            show_time, ' ', run_state)
        if r['return'] > 0:
            return r

    # For updating meta from update_meta_if_env
    r = self_module.update_state_from_meta(
        meta,
        deps=[],
        post_deps=[],
        prehook_deps=[],
        posthook_deps=[],
        new_env_keys=[],
        new_state_keys=[],
        run_state=run_state,
        i=i)
    if r['return'] > 0:
        return r

    # Skip scripts marked as non-runnable
    if not docker_settings.get('run', True) and not i.get(
            'docker_run_override', False):
        logger.info("docker.run set to False in meta.yaml")
        return {'return': 0, 'warning': 'Docker run is set to false in script meta'}

    if is_true(docker_settings.get('pass_docker_to_script', False)):
        logger.info("Docker 'run' is passed to the run script")
        i['docker'] = True
        r = self_module.run(i)
        return r

    # Regenerate Dockerfile if required
    if regenerate_docker_file:
        r = dockerfile(self_module, input_i)
        if r['return'] > 0:
            return r

    # Ensure Docker is available
    r = self_module.action_object.access(
        {'action': 'run', 'automation': 'script', 'tags': "get,docker", 'quiet': True})
    if r['return'] > 0:
        return r

    r = self_module._update_env_from_input(env, i)
    if r['return'] > 0:
        return r

    # Prepare Docker-specific inputs
    docker_inputs, dockerfile_path = prepare_docker_inputs(
        i, docker_settings, script, True, self_module.action_object)

    if docker_inputs is None:
        return {'return': 1, 'error': 'Error preparing Docker inputs'}

    docker_input_mapping = docker_settings.get('input_mapping')

    # Update env based on docker_input_mapping if they are in input
    if docker_input_mapping and i:
        env.update({docker_input_mapping[key]: i[key]
                    for key in docker_input_mapping if key in i})

    if docker_inputs.get('user'):
        docker_settings['user'] = docker_inputs['user']

    # Handle environment variable-based mounts
    res = process_mounts(
        mounts,
        env,
        docker_settings,
        f_run_cmd,
        run_state)
    if res['return'] > 0:
        return res
    docker_inputs['mounts'] = res['mounts']
    container_env_string = res['container_env_string']

    res = update_docker_environment(
        docker_settings, env, self_module.host_env_keys, container_env_string)
    if res['return'] > 0:
        return res

    # Generate the run command
    r = regenerate_script_cmd({'script_uid': script_uid,
                               'script_alias': script_alias,
                               'tags': tags,
                               'run_cmd': f_run_cmd})
    if r['return'] > 0:
        return r
    final_run_cmd = f"""{r['run_cmd_string']} {container_env_string} --docker_run_deps """

    # Execute the Docker container
    mlc_docker_input = {
        'action': 'run', 'target': 'script', 'tags': 'run,docker,container',
        'rebuild': rebuild_docker_image,
        'env': env,
        'script_tags': i.get('tags'), 'run_cmd': final_run_cmd,
        'quiet': True, 'real_run': True, 'add_deps_recursive': {'build-docker-image': {'dockerfile': dockerfile_path}}
    }
    utils.merge_dicts({'dict1': mlc_docker_input,
                       'dict2': docker_inputs,
                       'append_lists': True,
                       'append_unique': True})

    r = self_module.action_object.access(mlc_docker_input)
    if r['return'] > 0:
        return r

    return {'return': 0}
