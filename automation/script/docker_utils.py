import os
from mlc import utils
from utils import *
from pathlib import PureWindowsPath, PurePosixPath, Path
from script.docker_utils import *
import copy

def convert_to_abs_path(path):
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    return path

def process_mounts(mounts, env, docker_settings, f_run_cmd):
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
    if 'mounts' in docker_settings:
        mounts.extend(docker_settings['mounts'])

    docker_input_mapping = docker_settings.get("input_mapping", {})
    container_env_string = ""

    for index in range(len(mounts)):
        mount = mounts[index]

        # Locate the last ':' to separate the mount into host and container
        # paths
        j = mount.rfind(':')
        if j <= 0:
            return {
                'return': 1,
                'error': f"Can't find separator ':' in the mount string: {mount}"
            }

        host_mount, container_mount = mount[:j], mount[j + 1:]
        new_host_mount = host_mount
        new_container_mount = container_mount
        host_env_key, container_env_key = None, str(container_mount)

        # Process host mount for environment variables
        host_placeholders = re.findall(r'\${{ (.*?) }}', host_mount)
        if host_placeholders:
            for placeholder in host_placeholders:
                if placeholder in env:
                    host_env_key = placeholder
                    new_host_mount = get_host_path(env[placeholder])
                else:  # Skip mount if variable is missing
                    mounts[index] = None
                    break

        # Process container mount for environment variables
        container_placeholders = re.findall(r'\${{ (.*?) }}', container_mount)
        if container_placeholders:
            for placeholder in container_placeholders:
                if placeholder in env:
                    new_container_mount, container_env_key = get_container_path(
                        env[placeholder], docker_settings.get('user', 'mlcuser'))
                else:  # Skip mount if variable is missing
                    mounts[index] = None
                    break
        # Skip further processing if the mount was invalid
        if mounts[index] is None:
            continue

        # Update mount entry
        mounts[index] = f"{new_host_mount}:{new_container_mount}"

        # Update container environment string and mappings
        if host_env_key:
            container_env_string += f" --env.{host_env_key}={container_env_key} "
            for key, value in docker_input_mapping.items():
                if value == host_env_key:
                    f_run_cmd[key] = container_env_key

    # Remove invalid mounts and construct mount string
    mounts = [item for item in mounts if item is not None]

    return {'return': 0, 'mounts': mounts,
            'container_env_string': container_env_string}


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
        "mlc_repos", "skip_mlc_sys_upgrade", "extra_sys_deps", "image_name",
        "gh_token", "fake_run_deps", "run_final_cmds", "real_run", "copy_files", "path", "user"
    ]

    if run_stage:
        keys += [
            "skip_run_cmd", "pre_run_cmds", "run_cmd_prefix", "all_gpus", "num_gpus", "device", "gh_token",
            "port_maps", "shm_size", "pass_user_id", "pass_user_group", "extra_run_args", "detached", "interactive",
            "dt", "it", "use_host_group_id", "use_host_user_id", "keep_detached", "reuse_existing", "use_google_dns"
        ]
    # Collect Dockerfile inputs
    docker_inputs = {
        key: input_params.get(
            f"docker_{key}", docker_settings.get(
                key, get_docker_default(key)))
        for key in keys
        if (value := input_params.get(f"docker_{key}", docker_settings.get(key, get_docker_default(key)))) is not None
    }

    if is_true(docker_inputs.get('detached', docker_inputs.get('dt', ''))):
        docker_inputs['interactive'] = False
        docker_inputs['detached'] = True
    elif is_true(docker_inputs.get('interactive', docker_inputs.get('it', ''))):
        docker_inputs['interactive'] = True
        docker_inputs['detached'] = False

    for key in ["dt", "it"]:
        if docker_inputs.get(key):
            del (docker_inputs[key])

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


def update_docker_environment(docker_settings, env, container_env_string):
    """
    Updates the Docker environment variables and build arguments.

    Args:
        docker_settings (dict): Docker configuration settings.
        env (dict): The environment dictionary to update.
        container_env_string (str): A string to store Docker container environment variable options.

    Returns:
        dict: A dictionary with a return code indicating success or failure.
    """
    # Define proxy-related environment variable keys to propagate
    proxy_keys = [
        "ftp_proxy", "FTP_PROXY",
        "http_proxy", "HTTP_PROXY",
        "https_proxy", "HTTPS_PROXY",
        "no_proxy", "NO_PROXY",
        "socks_proxy", "SOCKS_PROXY",
        "GH_TOKEN"
    ]

    # Ensure the '+ CM_DOCKER_BUILD_ARGS' key exists in the environment
    if '+ MLC_DOCKER_BUILD_ARGS' not in env:
        env['+ MLC_DOCKER_BUILD_ARGS'] = []

    # Add proxy environment variables to Docker build arguments and container
    # environment string
    for proxy_key in proxy_keys:
        proxy_value = os.environ.get(proxy_key)
        if proxy_value:
            container_env_string += f" --env.{proxy_key}={proxy_value} "
            env['+ MLC_DOCKER_BUILD_ARGS'].append(f"{proxy_key}={proxy_value}")

    # Add host group ID if specified in the Docker settings and not on Windows
    if not is_false(docker_settings.get('pass_group_id')) and os.name != 'nt':
        env['+ MLC_DOCKER_BUILD_ARGS'].append(
            f"GID=\\\" $(id -g $USER) \\\""
        )

    # Add host user ID if specified in the Docker settings and not on Windows
    if not is_false(docker_settings.get(
            'use_host_user_id')) and os.name != 'nt':
        env['+ MLC_DOCKER_BUILD_ARGS'].append(
            f"UID=\\\" $(id -u $USER) \\\""
        )

    return {'return': 0}


def update_container_paths(path, mounts=None, force_target_path=''):
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
        mount_entry = f"""{os.path.dirname(host_path)}: {os.path.dirname(container_path)}"""
    else:
        mount_entry = f"""{host_path}:{container_path}"""

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
                if full_key in ['s', 'v']:
                    command_line += f" -{full_key}"
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
        "use_host_user_id": True,
        "use_host_group_id": True,
        "keep_detached": False,
    }
    if key in defaults:
        return defaults[key]
    return None


def get_host_path(value):
    # convert relative path to absolute path
    value = convert_to_abs_path(value)

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
    import getpass
    cur_user = getpass.getuser()
    if not cur_user or cur_user == '':
        cur_user = os.environ.get('USER', 'mlcuser')

    tmp_dep_cached_path = i['tmp_dep_cached_path']
    value_mnt, value_env = get_container_path(
        tmp_dep_cached_path, cur_user)
    return {'return': 0, 'value_mnt': value_mnt, 'value_env': value_env}


def get_container_path(value, username="mlcuser"):
    # convert relative path to absolute path
    value = convert_to_abs_path(value)

    path_split = value.split(os.sep)
    if len(path_split) == 1:
        return value, value

    new_value = ''
    if "cache" in path_split and "local" in path_split:
        new_path_split = ["", "home", username, "MLC", "repos"]
        repo_entry_index = path_split.index("local")
        if len(path_split) >= repo_entry_index + 3:
            new_path_split1 = new_path_split + \
                path_split[repo_entry_index:repo_entry_index + 3]
            new_path_split2 = new_path_split + path_split[repo_entry_index:]
            return "/".join(new_path_split1), "/".join(new_path_split2)
    else:
        orig_path, target_path = update_container_paths(path=value)
        return target_path, target_path
