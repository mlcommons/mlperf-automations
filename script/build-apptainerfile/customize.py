from mlc import utils
import os
import json
import re
import shutil
from utils import *


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    state = i['state']
    logger = i['automation'].logger

    if os_info['platform'] == 'windows':
        return {
            'return': 1,
            'error': 'Apptainer definition file generation is not supported on Windows.'}

    path = i['run_script_input']['path']

    with open(os.path.join(path, "apptainerinfo.json")) as f:
        config = json.load(f)

    apptainer_os = env.get(
        'MLC_APPTAINER_OS', env.get(
            'MLC_DOCKER_OS', 'ubuntu'))
    env['MLC_APPTAINER_OS'] = apptainer_os

    supported_distros = list(config.get('distros', {}).keys())
    if apptainer_os not in supported_distros:
        return {
            'return': 1,
            'error': f"Specified OS: {apptainer_os}. Supported: {', '.join(supported_distros)}"}

    distro_config = config['distros'][apptainer_os]
    known_versions = distro_config.get('versions', {})

    if not env.get("MLC_APPTAINER_OS_VERSION", ""):
        env["MLC_APPTAINER_OS_VERSION"] = env.get(
            'MLC_DOCKER_OS_VERSION',
            distro_config.get('default_version', '24.04'))

    # Gracefully handle unlisted host versions (e.g. release candidates or
    # not-yet-added releases) by falling back to the distro's default version.
    if not env.get('MLC_APPTAINER_IMAGE_BASE', '') and known_versions and \
            env['MLC_APPTAINER_OS_VERSION'] not in known_versions:
        fallback_version = distro_config.get(
            'default_version', list(known_versions.keys())[-1])
        logger.warning(
            f"Version \"{env['MLC_APPTAINER_OS_VERSION']}\" not listed for "
            f"\"{apptainer_os}\"; falling back to \"{fallback_version}\".")
        env['MLC_APPTAINER_OS_VERSION'] = fallback_version

    apptainer_os_version = env['MLC_APPTAINER_OS_VERSION']

    bootstrap_from = get_value(env, config, 'FROM', 'MLC_APPTAINER_IMAGE_BASE')
    if not bootstrap_from:
        return {
            'return': 1,
            'error': f'Version "{apptainer_os_version}" is not supported for "{apptainer_os}"'}

    # Determine bootstrap type and From value
    if bootstrap_from.startswith('docker://'):
        bootstrap_type = 'docker'
        bootstrap_uri = bootstrap_from[len('docker://'):]
    elif bootstrap_from.startswith('library://'):
        bootstrap_type = 'library'
        bootstrap_uri = bootstrap_from[len('library://'):]
    elif bootstrap_from.startswith('oras://'):
        bootstrap_type = 'oras'
        bootstrap_uri = bootstrap_from[len('oras://'):]
    elif os.path.exists(bootstrap_from) or bootstrap_from.endswith('.sif'):
        bootstrap_type = 'localimage'
        bootstrap_uri = bootstrap_from
    else:
        bootstrap_type = 'docker'
        bootstrap_uri = bootstrap_from

    # Handle mlc_mlops Repository
    if env.get("MLC_REPO_PATH", "") != "":
        use_copy_repo = True
        mlc_repo_path = os.path.abspath(env["MLC_REPO_PATH"])
        if not os.path.exists(mlc_repo_path):
            return {
                'return': 1,
                'error': f"Specified MLC_REPO_PATH does not exist: {mlc_repo_path}"}
    else:
        use_copy_repo = False
        if env.get("MLC_MLOPS_REPO", "") != "":
            mlc_mlops_repo = env["MLC_MLOPS_REPO"]
            git_link_pattern = r'^(https?://github\.com/([^/]+)/([^/]+)(?:\.git)?|git@github\.com:([^/]+)/([^/]+)(?:\.git)?)$'
            if match := re.match(git_link_pattern, mlc_mlops_repo):
                if match.group(2) and match.group(3):
                    repo_owner = match.group(2)
                    repo_name = match.group(3)
                elif match.group(4) and match.group(5):
                    repo_owner = match.group(4)
                    repo_name = match.group(5)
                mlc_mlops_repo = f"{repo_owner}@{repo_name}"
        else:
            mlc_mlops_repo = "mlcommons@mlperf-automations"

    # Copy the host's registered MLC repos into the image instead of pulling
    # them at build time (triggered by --apptainer_host_mlc_repos).
    use_host_repos = is_true(env.get('MLC_APPTAINER_HOST_MLC_REPOS', ''))
    host_repos_to_copy = []
    if use_host_repos:
        for repo in i['automation'].action_object.repos:
            if repo.meta.get('alias', '') == 'local':
                continue
            repo_path = repo.path
            if not repo_path or not os.path.isdir(repo_path):
                continue
            repo_path = os.path.abspath(repo_path)
            host_repos_to_copy.append(
                (os.path.dirname(repo_path),
                 os.path.basename(os.path.normpath(repo_path))))
        if not host_repos_to_copy:
            logger.warning(
                "MLC_APPTAINER_HOST_MLC_REPOS set but no host repos found; "
                "falling back to pulling the default repo.")
            use_host_repos = False

    mlc_mlops_repo_branch_string = f" --branch={env.get('MLC_MLOPS_REPO_BRANCH', 'dev')}"

    if env.get('MLC_APPTAINERFILE_WITH_PATH', '') == '':
        env['MLC_APPTAINERFILE_WITH_PATH'] = os.path.join(
            os.getcwd(), "apptainer.def")

    def_file_path = env['MLC_APPTAINERFILE_WITH_PATH']
    def_file_dir = os.path.dirname(def_file_path)

    if def_file_dir != '':
        os.makedirs(def_file_dir, exist_ok=True)

    python = get_value(env, config, 'PYTHON', 'MLC_APPTAINERFILE_PYTHON')
    if not python:
        python = 'python3'

    pkg_update_cmd = get_value(env, config, 'package-manager-update-cmd')
    pkg_get_cmd = get_value(env, config, 'package-manager-get-cmd')
    packages = get_value(env, config, 'packages')
    pip_packages = get_value(env, config, 'python-packages')

    with open(def_file_path, "w") as f:
        # Header
        f.write(f"Bootstrap: {bootstrap_type}\n")
        f.write(f"From: {bootstrap_uri}\n")
        f.write("\n")

        # Labels
        f.write("%labels\n")
        f.write("    maintainer MLC Automation Framework\n")
        f.write(f"    os {apptainer_os}\n")
        f.write(f"    os_version {apptainer_os_version}\n")
        f.write("\n")

        # Environment
        f.write("%environment\n")
        f.write("    export TZ=US/Pacific\n")
        f.write("    export PATH=$HOME/.local/bin:$PATH\n")

        dockerfile_build_env = state.get('dockerfile_build_env', {})
        for key, value in dockerfile_build_env.items():
            f.write(f"    export {key}=\"{value}\"\n")
        f.write("\n")

        # Post (main install section)
        f.write("%post\n")
        f.write("    # Set timezone\n")
        f.write("    export TZ=US/Pacific\n")
        f.write("    export DEBIAN_FRONTEND=noninteractive\n")
        f.write(
            "    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ >/etc/timezone\n")
        f.write("\n")

        f.write("    # Install system dependencies\n")
        f.write(f"    {pkg_update_cmd}\n")
        f.write(f"    {pkg_get_cmd} {' '.join(packages)}\n")
        f.write("\n")

        if env.get('MLC_APPTAINER_EXTRA_SYS_DEPS', '') != '':
            f.write(f"    {env['MLC_APPTAINER_EXTRA_SYS_DEPS']}\n")
            f.write("\n")

        f.write("    # Install python packages\n")
        f.write(f"    {python} -m venv /opt/venv/mlcflow\n")
        f.write("    . /opt/venv/mlcflow/bin/activate\n")
        f.write(f"    {python} -m pip install --upgrade pip setuptools\n")
        f.write(f"    {python} -m pip install {' '.join(pip_packages)}\n")
        f.write("\n")

        f.write("    # Download MLC repo for scripts\n")
        if use_host_repos:
            # Host repos are copied in via %setup; just register them.
            f.write(
                "    for d in /opt/mlc_host_repos/*/; do mlc add repo \"$d\" --quiet 2>/dev/null || true; done\n")
            f.write(
                "    for d in /opt/mlc_host_repos/*/; do [ -d \"$d/.git\" ] && git -C \"$d\" update-index --refresh 2>/dev/null || true; done\n")
        elif use_copy_repo:
            repo_name = os.path.basename(mlc_repo_path)
            # Set MLC_REPOS to match the runtime path so repos.json is created
            # at the correct location for the container's runtime env.
            f.write(f"    export MLC_REPOS=/opt/mlc_repo/{repo_name}\n")
            # Register each subdirectory as an individual repo (the parent
            # dir is a MLC_REPOS directory, not a single repo).
            f.write(
                f"    for d in /opt/mlc_repo/{repo_name}/*/; do mlc add repo \"$d\" --quiet 2>/dev/null || true; done\n")
            # Refresh git index stat cache — tar copy into SIF changes timestamps,
            # making git see all files as modified. Without this, mlc pull repo
            # fails with "local changes" inside the container.
            f.write(
                f"    for d in /opt/mlc_repo/{repo_name}/*/; do [ -d \"$d/.git\" ] && git -C \"$d\" update-index --refresh 2>/dev/null || true; done\n")
        else:
            x = env.get('MLC_APPTAINER_ADD_FLAG_TO_MLC_MLOPS_REPO', '')
            if x != '':
                x = ' ' + x
            f.write(
                f"    mlc pull repo {mlc_mlops_repo}{mlc_mlops_repo_branch_string}{x} --quiet\n")

        # Extra repos
        extra_repos = env.get('MLC_APPTAINER_EXTRA_MLC_REPOS', '')
        if extra_repos != '':
            for y in extra_repos.split(','):
                f.write(f"    {y}\n")

        f.write("    mlc run script --tags=get,sys-utils-mlc --quiet\n")
        f.write("\n")

        # Pre-run commands
        if 'MLC_APPTAINER_PRE_RUN_COMMANDS' in env:
            f.write("    # Pre-run commands\n")
            for pre_cmd in env['MLC_APPTAINER_PRE_RUN_COMMANDS']:
                f.write(f"    {pre_cmd}\n")
            f.write("\n")

        # Main run command
        run_cmd_extra = " " + \
            env.get('MLC_APPTAINER_RUN_CMD_EXTRA', '').replace(":", "=")
        if 'MLC_APPTAINER_RUN_CMD' not in env:
            if 'MLC_APPTAINER_RUN_SCRIPT_TAGS' not in env:
                env['MLC_APPTAINER_RUN_CMD'] = "mlcr --help"
            else:
                env['MLC_APPTAINER_RUN_CMD'] = "mlcr " + \
                    env['MLC_APPTAINER_RUN_SCRIPT_TAGS'] + ' --quiet'

        f.write("    # Run commands\n")
        cmd = env['MLC_APPTAINER_RUN_CMD']
        # Mirror build-dockerfile: fake the deps during the build %post so that
        # runtime-only deps (e.g. compilers on host bind mounts, absent in the
        # build sandbox) are not executed. The shared docker: meta lands
        # MLC_DOCKER_FAKE_DEPS in state['dockerfile_env'].
        enable_fake_deps = (
            is_true(env.get('MLC_DOCKER_FAKE_DEPS', '')) or
            is_true(env.get('MLC_APPTAINER_FAKE_DEPS', '')) or
            is_true(state.get('dockerfile_env', {}).get(
                'MLC_DOCKER_FAKE_DEPS', '')))
        fake_deps_str = " --fake_deps" if enable_fake_deps else ""
        # Propagate build-scoped env (e.g. MLC_RUN_STATE_DOCKER) onto the run
        # command as --env.KEY=VAL so runtime-only deps skip during the build,
        # mirroring build-dockerfile. Without MLC_RUN_STATE_DOCKER, deps that
        # point at runtime bind mounts execute in the build sandbox and fail.
        dockerfile_env = state.get('dockerfile_env', {})
        dockerfile_env_input_string = ""
        for env_key in dockerfile_env:
            dockerfile_env_input_string += " --env." + env_key + "=" + \
                str(dockerfile_env[env_key]).replace("\n", "\\n")
        f.write(
            f"    {cmd} --fake_run{fake_deps_str}"
            f"{dockerfile_env_input_string}{run_cmd_extra}\n")
        f.write("\n")

        # Post-run commands
        if 'MLC_APPTAINER_POST_RUN_COMMANDS' in env:
            f.write("    # Post-run commands\n")
            for post_cmd in env['MLC_APPTAINER_POST_RUN_COMMANDS']:
                f.write(f"    {post_cmd}\n")
            f.write("\n")

        # Copy section for local repo (use %setup with tar to handle symlinks
        # gracefully)
        if use_host_repos:
            f.write("%setup\n")
            f.write("    mkdir -p ${APPTAINER_ROOTFS}/opt/mlc_host_repos\n")
            for parent_dir, repo_name in host_repos_to_copy:
                f.write(
                    f"    tar -C {parent_dir} --exclude=repos.json --exclude='index_*.json' --exclude=local --exclude=modified_times.json --exclude='*.sif' -cf - {repo_name} | tar -xf - -C ${{APPTAINER_ROOTFS}}/opt/mlc_host_repos/\n")
            f.write("    chmod -R 777 ${APPTAINER_ROOTFS}/opt/mlc_host_repos\n")
            f.write("\n")
        elif use_copy_repo:
            repo_name = os.path.basename(mlc_repo_path)
            f.write("%setup\n")
            f.write(f"    mkdir -p ${{APPTAINER_ROOTFS}}/opt/mlc_repo\n")
            f.write(
                f"    tar -C {mlc_repo_path}/.. --exclude=repos.json --exclude='index_*.json' --exclude=local --exclude=modified_times.json --exclude='*.sif' -cf - {repo_name} | tar -xf - -C ${{APPTAINER_ROOTFS}}/opt/mlc_repo/\n")
            f.write(f"    chmod -R 777 ${{APPTAINER_ROOTFS}}/opt/mlc_repo\n")
            f.write("\n")

        # Runscript
        f.write("%runscript\n")
        f.write("    . /opt/venv/mlcflow/bin/activate\n")
        f.write("    exec \"$@\"\n")
        f.write("\n")

        # Help
        f.write("%help\n")
        f.write(
            f"    Apptainer container based on {apptainer_os}:{apptainer_os_version}\n")
        f.write("    Built with MLC workflow automation framework.\n")
        f.write("    Run with: apptainer run <image.sif> <command>\n")

    logger.info(f"Apptainer definition file written at {def_file_path}")

    return {'return': 0}


def get_value(env, config, key, env_key=None):
    if not env_key:
        env_key = key

    if env.get(env_key, None) is not None:
        return env[env_key]

    apptainer_os = env['MLC_APPTAINER_OS']
    apptainer_os_version = env['MLC_APPTAINER_OS_VERSION']

    distro_config = config['distros'].get(apptainer_os, {})
    version_meta = distro_config.get(
        'versions', {}).get(
        apptainer_os_version, {})
    if key in version_meta:
        return version_meta[key]

    if key in distro_config:
        return distro_config[key]

    if key in config:
        return config[key]

    return None
