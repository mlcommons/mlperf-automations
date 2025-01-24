import os
from mlc import utils
from utils import *
import logging
from pathlib import PureWindowsPath, PurePosixPath
from script.docker_utils import *
import copy


def process_mounts(mounts, env, i, docker_settings):
    """
    Processes and updates the Docker mounts based on the provided inputs and environment variables.

    Args:
        mounts: List of existing mount configurations.
        env: Current environment variables dictionary.
        i: Input dictionary with user-specified overrides.
        docker_settings: Docker-specific settings from the script's metadata.

    Returns:
        Updated mounts list or None in case of an error.
    """
    try:
        # Add mounts specified via `env` variables
        for mount_key in docker_settings.get('env_mounts', []):
            mount_path = env.get(mount_key, '')
            if mount_path:
                mounts.append(mount_path)

        # Include user-specified additional mounts
        if 'docker_additional_mounts' in i:
            mounts.extend(i['docker_additional_mounts'])

        return mounts
    except Exception as e:
        logging.error(f"Error processing mounts: {e}")
        return None


def prepare_docker_inputs(input_params, docker_settings,
                          script_path, run_stage=False):
    """
    Prepares Docker-specific inputs such as Dockerfile path and runtime options.

    Args:
        i: Input dictionary with user-specified overrides.
        docker_settings: Docker-specific settings from the script's metadata.
        script_path: Path to the script being executed.

    Returns:
        Tuple with Docker inputs dictionary and Dockerfile path or None in case of an error.
    """

    keys = [
        "mlc_repo", "mlc_repo_branch", "base_image", "os", "os_version",
        "mlc_repos", "skip_mlc_sys_upgrade", "extra_sys_deps",
        "gh_token", "fake_run_deps", "run_final_cmds", "real_run", "copy_files", "path"
    ]

    if run_stage:
        keys += [
            "skip_run_cmd", "pre_run_cmds", "run_cmd_prefix", "all_gpus", "num_gpus", "device", "gh_token",
            "port_maps", "shm_size", "pass_user_id", "pass_user_group", "extra_run_args", "detached", "interactive",
            "dt", "it"
        ]
    # Collect Dockerfile inputs
    docker_inputs = {
        key: input_params.get(
            f"docker_{key}", docker_settings.get(
                key, get_docker_default(key)))
        for key in keys
        if (value := input_params.get(f"docker_{key}", docker_settings.get(key, get_docker_default(key)))) is not None
    }

    if docker_inputs.get('detached', docker_inputs.get('dt')):
        docker_inputs['interactive'] = False
        docker_inputs['detached'] = True

    # Determine Dockerfile suffix and path
    docker_base_image = docker_inputs.get('base_image')
    docker_path = docker_inputs.get('path')
    if not docker_path:
        docker_path = script_path
    docker_filename_suffix = (
        docker_base_image.replace('/', '-').replace(':', '-')
        if docker_base_image else f"{docker_inputs['os']}_{docker_inputs['os_version']}"
    )
    dockerfile_path = os.path.join(
        docker_path,
        'dockerfiles',
        f"{docker_filename_suffix}.Dockerfile")

    docker_inputs['file_path'] = dockerfile_path

    return docker_inputs, dockerfile_path


def update_docker_paths(path, mounts=None, force_target_path=''):
    """
    Update and return the absolute paths for a given host path and its container equivalent.
    Optionally updates a mounts list with the mapping of host and container paths.

    :param path: The original host path.
    :param mounts: A list to store host-to-container path mappings in the format "host_path:container_path".
    :param force_target_path: Optional; overrides the default container path target.
    :return: A tuple of (original_host_path, container_path).
    """
    if not path:
        return '', ''  # Return empty paths if no path is provided.

    # Normalize and resolve the absolute path.
    host_path = os.path.abspath(path)
    container_path = host_path  # Default to the same path for containers.

    # Handle Windows-specific path conversion for Docker.
    if os.name == 'nt':
        windows_path = PureWindowsPath(host_path)
        container_path = str(PurePosixPath('/', *windows_path.parts[1:]))

    # Ensure the container path starts with a forward slash.
    if not container_path.startswith('/'):
        container_path = '/' + container_path

    # Prepend default container mount base unless overridden.
    container_path = '/mlc-mount' + \
        container_path if not force_target_path else force_target_path

    # Determine the mount string based on whether the path is a file or
    # directory.
    if os.path.isfile(host_path) or not os.path.isdir(host_path):
        mount_entry = f"{
            os.path.dirname(host_path)}: {
            os.path.dirname(container_path)}"
    else:
        mount_entry = f"{host_path}:{container_path}"

    # Add the mount entry to the mounts list if it's not already present.
    if mounts is not None:
        if all(mount.lower() != mount_entry.lower() for mount in mounts):
            mounts.append(mount_entry)

    return host_path, container_path


def regenerate_script_cmd(i):

    script_uid = i['script_uid']
    script_alias = i['script_alias']
    tags = i['tags']
    docker_settings = i.get('docker_settings', {})
    fake_run = i.get('fake_run', False)

    i_run_cmd = i['run_cmd']

    # Remove environment variables with host path values
    if 'env' in i_run_cmd:
        env = i_run_cmd['env']
        for key in list(env):
            value = env[key]

            # Check if the value is a string containing the specified paths
            if isinstance(value, str) and (
                    os.path.join("local", "cache", "") in value or
                    os.path.join("MLC", "repos", "") in value
            ):
                del env[key]

            # Check if the value is a list and remove matching items
            elif isinstance(value, list):
                # Identify values to remove
                values_to_remove = [
                    val for val in value
                    if isinstance(val, str) and (
                        os.path.join("local", "cache", "") in val or
                        os.path.join("MLC", "repos", "") in val
                    )
                ]

                # Remove key if all values match; otherwise, filter the list
                if len(values_to_remove) == len(value):
                    del env[key]
                else:
                    env[key] = [
                        val for val in value if val not in values_to_remove]

    docker_run_cmd_prefix = i.get('docker_run_cmd_prefix', '')

    # Regenerate command from dictionary input
    run_cmd = 'mlcr'

    skip_input_for_fake_run = docker_settings.get(
        'skip_input_for_fake_run', [])
    add_quotes_to_keys = docker_settings.get('add_quotes_to_keys', [])

    def rebuild_flags(
            command_dict,
            is_fake_run,
            skip_keys_for_fake_run,
            quote_keys,
            prefix
    ):
        """
        Recursively rebuilds command-line flags from a dictionary of inputs.

        :param command_dict: Dictionary containing command-line keys and values.
        :param is_fake_run: Boolean indicating if this is a fake run.
        :param skip_keys_for_fake_run: List of keys to skip in fake run mode.
        :param quote_keys: List of keys that require values to be quoted.
        :param prefix: String to prepend to keys for hierarchical keys.
        :return: A reconstructed command-line string.
        """
        command_line = ""

        # Sort keys to ensure 'tags' appears first if present.
        keys = sorted(command_dict.keys(), key=lambda x: x != "tags")

        for key in keys:
            # Construct the full key with the prefix.
            full_key = f"{prefix}.{key}" if prefix else key

            # Skip keys marked for exclusion in fake run mode.
            if is_fake_run and full_key in skip_keys_for_fake_run:
                continue

            value = command_dict[key]
            quote = '\\"' if full_key in quote_keys else ""

            # Recursively process nested dictionaries.
            if isinstance(value, dict):
                command_line += rebuild_flags(
                    value,
                    is_fake_run,
                    skip_keys_for_fake_run,
                    quote_keys,
                    full_key
                )
            # Process lists by concatenating values with commas.
            elif isinstance(value, list):
                list_values = ",".join(
                    f"{quote}{str(item)}{quote}" for item in value)
                command_line += f" --{full_key},={list_values}"
            # Process scalar values.
            else:
                command_line += f" --{full_key}={quote}{str(value)}{quote}"

        return command_line

    run_cmd += rebuild_flags(i_run_cmd,
                             fake_run,
                             skip_input_for_fake_run,
                             add_quotes_to_keys,
                             '')

    run_cmd = docker_run_cmd_prefix + ' && ' + \
        run_cmd if docker_run_cmd_prefix != '' else run_cmd

    return {'return': 0, 'run_cmd_string': run_cmd}


def get_docker_default(key):
    defaults = {
        "mlc_repo": "mlcommons@mlperf-automations",
        "mlc_repo_branch": "dev",
        "os": "ubuntu",
        "os_version": "24.04",
        "fake_run_deps": False,
        "run_final_cmds": [],
        "skip_run_cmd": False,
        "image_tag_extra": "-latest",
        "skip_run_cmd": False,
        "pre_run_cmds": [],
        "run_cmd_prefix": '',
        "port_maps": [],
        "detached": False,
        "interactive": True
    }
    if key in defaults:
        return defaults[key]
    return None


def get_host_path(value):
    path_split = value.split(os.sep)
    if len(path_split) == 1:
        return value

    new_value = ''
    if "cache" in path_split and "local":
        repo_entry_index = path_split.index("local")
        if len(path_split) >= repo_entry_index + 3:
            return os.sep.join(path_split[0:repo_entry_index + 3])

    return value


def get_container_path_script(i):
    tmp_dep_cached_path = i['tmp_dep_cached_path']
    value_mnt, value_env = get_container_path(tmp_dep_cached_path)
    return {'return': 0, 'value_mnt': value_mnt, 'value_env': value_env}


def get_container_path(value):
    path_split = value.split(os.sep)
    if len(path_split) == 1:
        return value

    new_value = ''
    if "cache" in path_split and "local" in path_split:
        new_path_split = ["", "home", "mlcuser", "MLC", "repos"]
        repo_entry_index = path_split.index("local")
        if len(path_split) >= repo_entry_index + 3:
            new_path_split1 = new_path_split + \
                path_split[repo_entry_index:repo_entry_index + 3]
            new_path_split2 = new_path_split + path_split[repo_entry_index:]
            return "/".join(new_path_split1), "/".join(new_path_split2)
    else:
        orig_path, target_path = update_path_for_docker(path=value)
        return target_path, target_path
