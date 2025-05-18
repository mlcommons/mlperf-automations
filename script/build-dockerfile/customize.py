from mlc import utils
import os
import mlc
import json
import re
import shutil
from utils import *


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger

    if env["MLC_DOCKER_OS"] not in ["ubuntu", "rhel", "arch"]:
        return {
            'return': 1, 'error': f"Specified docker OS: {env['MLC_DOCKER_OS']}. Currently only ubuntu, rhel and arch are supported in CM docker"}

    path = i['run_script_input']['path']

    with open(os.path.join(path, "dockerinfo.json")) as f:
        config = json.load(f)

    build_args = []
    build_args_default = {}
    input_args = []
    copy_files = []
    automation = i['automation']

    # print(env['MLC_DOCKER_RUN_SCRIPT_TAGS'])
    if env.get('MLC_DOCKER_RUN_SCRIPT_TAGS', '') != '':
        script_tags = env['MLC_DOCKER_RUN_SCRIPT_TAGS']
        found_scripts = automation.action_object.access(
            {'action': 'search', 'target': 'script', 'tags': script_tags})
        scripts_list = found_scripts['list']

        if not scripts_list:
            return {'return': 1,
                    'error': 'No automation script found for tags=' + script_tags}

        if len(scripts_list) > 1:
            return {
                'return': 1, 'error': 'More than one scripts found for tags ' + script_tags}

        script = scripts_list[0]
        input_mapping = script.meta.get('input_mapping', {})
        default_env = script.meta.get('default_env', {})

        for input_, env_ in input_mapping.items():
            if input_ == "docker":
                continue
            arg = env_
            if env_ in default_env:  # other inputs to be done later
                arg = arg + "=" + str(default_env[env_])
                # build_args.append(arg)
                # input_args.append("--"+input_+"="+"$"+env_)

    if "MLC_DOCKER_OS_VERSION" not in env:
        env["MLC_DOCKER_OS_VERSION"] = "20.04"

    docker_image_base = get_value(env, config, 'FROM', 'MLC_DOCKER_IMAGE_BASE')
    if not docker_image_base:
        return {
            'return': 1, 'error': f"Version \"{env['MLC_DOCKER_OS_VERSION']}\" is not supported yet for \"{env['MLC_DOCKER_OS']}\" "}

    # Handle mlc_mlops Repository
    if env.get("MLC_REPO_PATH", "") != "":
        use_copy_repo = True
        mlc_repo_path = os.path.abspath(env["MLC_REPO_PATH"])

        if not os.path.exists(mlc_repo_path):
            return {
                'return': 1, 'error': f"Specified MLC_REPO_PATH does not exist: {mlc_repo_path}"}

        meta_yml_path = os.path.join(mlc_repo_path, "meta.yaml")
        if not os.path.isfile(meta_yml_path):
            return {
                'return': 1, 'error': f"meta.yaml not found in MLC_REPO_PATH: {mlc_repo_path}"}

        # Define the build context directory (where the Dockerfile will be)
        build_context_dir = os.path.dirname(
            env.get(
                'MLC_DOCKERFILE_WITH_PATH',
                os.path.join(
                    os.getcwd(),
                    "Dockerfile")))
        os.makedirs(build_context_dir, exist_ok=True)

        # Create mlc_repo directory relative to the build context
        repo_build_context_path = os.path.join(build_context_dir, "mlc_repo")

        # Remove existing directory if it exists
        if os.path.exists(repo_build_context_path):
            shutil.rmtree(repo_build_context_path)

        try:
            print(
                f"Copying repository from {mlc_repo_path} to {repo_build_context_path}")
            shutil.copytree(mlc_repo_path, repo_build_context_path)
        except Exception as e:
            return {
                'return': 1, 'error': f"Failed to copy repository to build context: {str(e)}"}

        if not os.path.isdir(repo_build_context_path):
            return {
                'return': 1, 'error': f"Repository was not successfully copied to {repo_build_context_path}"}

        # (Optional) Verify the copy
        if not os.path.isdir(repo_build_context_path):
            return {
                'return': 1, 'error': f"mlc_repo was not successfully copied to the build context at {repo_build_context_path}"}
        else:
            print(
                f"mlc_repo is present in the build context at {repo_build_context_path}")

        relative_repo_path = os.path.relpath(
            repo_build_context_path, build_context_dir)
    else:
        # MLC_REPO_PATH is not set; use mlc pull repo as before
        use_copy_repo = False

        if env.get("MLC_MLOPS_REPO", "") != "":
            mlc_mlops_repo = env["MLC_MLOPS_REPO"]
            # the below pattern matches both the HTTPS and SSH git link formats
            git_link_pattern = r'^(https?://github\.com/([^/]+)/([^/]+)(?:\.git)?|git@github\.com:([^/]+)/([^/]+)(?:\.git)?)$'
            if match := re.match(git_link_pattern, mlc_mlops_repo):
                if match.group(2) and match.group(3):
                    repo_owner = match.group(2)
                    repo_name = match.group(3)
                elif match.group(4) and match.group(5):
                    repo_owner = match.group(4)
                    repo_name = match.group(5)
                mlc_mlops_repo = f"{repo_owner}@{repo_name}"
                print(
                    f"Converted repo format from {env['MLC_MLOPS_REPO']} to {mlc_mlops_repo}")
        else:
            mlc_mlops_repo = "mlcommons@mlperf-automations"

    mlc_mlops_repo_branch_string = f" --branch={env['MLC_MLOPS_REPO_BRANCH']}"

    if env.get('MLC_DOCKERFILE_WITH_PATH', '') == '':
        env['MLC_DOCKERFILE_WITH_PATH'] = os.path.join(
            os.getcwd(), "Dockerfile")

    dockerfile_with_path = env['MLC_DOCKERFILE_WITH_PATH']
    dockerfile_dir = os.path.dirname(dockerfile_with_path)

    extra_dir = os.path.dirname(dockerfile_with_path)

    if extra_dir != '':
        os.makedirs(extra_dir, exist_ok=True)

    f = open(dockerfile_with_path, "w")
    EOL = env['MLC_DOCKER_IMAGE_EOL']
    f.write('FROM ' + docker_image_base + EOL)

    # Maintainers
    f.write(EOL)
    f.write(
        '# Automatically generated by the MLC workflow automation meta-framework' +
        EOL)
    f.write(EOL)

    f.write('LABEL github=""' + EOL)
    f.write('LABEL maintainer=""' + EOL)
    f.write('LABEL license=""' + EOL)

    f.write(EOL)

    image_label = get_value(env, config, 'LABEL', 'MLC_DOCKER_IMAGE_LABEL')
    if image_label:
        f.write('LABEL ' + image_label + EOL)
        f.write(EOL)

    shell = get_value(env, config, 'SHELL', 'MLC_DOCKER_IMAGE_SHELL')
    if shell:
        # f.write('SHELL ' + shell + EOL)
        f.write(EOL)

    for arg in config['ARGS_DEFAULT']:
        arg_value = config['ARGS_DEFAULT'][arg]
        f.write('ARG ' + f"{arg}={arg_value}" + EOL)

    for arg in config['ARGS']:
        f.write('ARG ' + arg + EOL)

    for build_arg in build_args:
        f.write('ARG ' + build_arg + EOL)

    for build_arg in sorted(build_args_default):
        v = build_args_default[build_arg]
        f.write('ARG ' + build_arg + '="' + str(v) + '"' + EOL)

    f.write(EOL)
    copy_cmds = []
    if 'MLC_DOCKER_COPY_FILES' in env:
        for copy_file in env['MLC_DOCKER_COPY_FILES']:
            copy_split = copy_file.split(":")
            if len(copy_split) != 2:
                return {
                    'return': 1, 'error': 'Invalid docker copy input {} given'.format(copy_file)}
            filename = os.path.basename(copy_split[0])
            if not os.path.exists(os.path.join(dockerfile_dir, filename)):
                shutil.copytree(
                    copy_split[0], os.path.join(
                        dockerfile_dir, filename))
            f.write('COPY ' + filename + " " + copy_split[1] + EOL)

    f.write(
        EOL +
        '# Notes: https://runnable.com/blog/9-common-dockerfile-mistakes' +
        EOL +
        '# Install system dependencies' +
        EOL)
    f.write(
        'RUN ' +
        get_value(
            env,
            config,
            'package-manager-update-cmd',
            'MLC_PACKAGE_MANAGER_UPDATE_CMD') +
        EOL)
    f.write('RUN ' + get_value(env, config, 'package-manager-get-cmd') + " " + " ".join(get_value(env, config,
                                                                                                  'packages')) + EOL)

    if env.get('MLC_DOCKER_EXTRA_SYS_DEPS', '') != '':
        f.write('RUN ' + env['MLC_DOCKER_EXTRA_SYS_DEPS'] + EOL)

    if env['MLC_DOCKER_OS'] == "ubuntu":
        if int(env['MLC_DOCKER_OS_VERSION'].split('.')[0]) >= 23:
            if "--break-system-packages" not in env.get(
                    'MLC_DOCKER_PIP_INSTALL_EXTRA_FLAGS', ''):
                env['MLC_DOCKER_PIP_INSTALL_EXTRA_FLAGS'] = " --break-system-packages"
    pip_extra_flags = env.get('MLC_DOCKER_PIP_INSTALL_EXTRA_FLAGS', '')

    f.write(EOL + '# Setup docker environment' + EOL)

    entry_point = get_value(
        env,
        config,
        'ENTRYPOINT',
        'MLC_DOCKER_IMAGE_ENTRYPOINT')
    if entry_point:
        f.write('ENTRYPOINT ' + entry_point + EOL)

    for key, value in config['ENV'].items():
        f.write('ENV ' + key + "=\"" + value + "\"" + EOL)
    for cmd in config['RUN_CMDS']:
        f.write('RUN ' + cmd + EOL)

    if env.get('MLC_MLPERF_IMPLEMENTATION', '') == "nvidia" and env.get(
            'MLC_MLPERF_INFERENCE_VERSION', '') == "5.0":
        f.write('ENV ' + 'ENV' + "=\"" + 'release' + "\"" + EOL)

    f.write(EOL + '# Setup docker user' + EOL)
    docker_user = get_value(env, config, 'USER', 'MLC_DOCKER_USER')
    docker_group = get_value(env, config, 'GROUP', 'MLC_DOCKER_GROUP')

    if env.get('MLC_CONTAINER_TOOL', '') == 'podman' and env.get(
            'MLC_DOCKER_USE_DEFAULT_USER', '') == '':
        env['MLC_DOCKER_USE_DEFAULT_USER'] = 'yes'

    if docker_user and not is_true(env.get('MLC_DOCKER_USE_DEFAULT_USER', '')):

        f.write('RUN groupadd -g $GID -o ' + docker_group + EOL)

        DOCKER_USER_ID = "-m -u $UID "
        DOCKER_GROUP = "-g $GID -o"

        user_shell = json.loads(shell)
        f.write(f"""RUN (id -u {docker_user} > /dev/null 2>&1 && usermod -u $UID {docker_user}) || useradd """ + DOCKER_USER_ID + DOCKER_GROUP + ' --create-home --shell ' + user_shell[0] + ' '
                + docker_user + EOL)
        f.write(
            'RUN echo "' +
            docker_user +
            ' ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers' +
            EOL)
        f.write('RUN usermod -g sudo mlcuser' + EOL)
        f.write('USER ' + docker_user + ":" + docker_group + EOL)
        f.write(f"""ENV HOME=/home/{docker_user}""" + EOL)

    else:
        f.write('ENV HOME=/root' + EOL)

    dockerfile_env = env.get('MLC_DOCKERFILE_ENV', {})
    dockerfile_env_input_string = ""
    for docker_env_key in dockerfile_env:
        dockerfile_env_input_string = dockerfile_env_input_string + " --env." + \
            docker_env_key + "=" + str(dockerfile_env[docker_env_key])

    workdir = env.get('WORKDIR', '')
    if workdir == '':
        workdir = f"""/home/{docker_user}"""

    if f"""/home/{docker_user}""" not in workdir or not is_true(
            env.get('MLC_DOCKER_USE_DEFAULT_USER', '')):
        f.write('WORKDIR ' + workdir + EOL)

    f.write(EOL + '# Install python packages' + EOL)
    python = get_value(env, config, 'PYTHON', 'MLC_DOCKERFILE_PYTHON')

    docker_use_virtual_python = env.get('MLC_DOCKER_USE_VIRTUAL_PYTHON', "yes")
    if not is_false(docker_use_virtual_python):
        f.write('RUN {} -m venv $HOME/venv/mlc'.format(python) + " " + EOL)
        f.write('ENV PATH="$HOME/venv/mlc/bin:$PATH"' + EOL)
    # f.write('RUN . /opt/venv/mlc/bin/activate' + EOL)

    f.write('ENV PATH="$PATH:$HOME/.local/bin"' + EOL)

    f.write(
        'RUN {} -m pip install '.format(python) +
        " ".join(
            get_value(
                env,
                config,
                'python-packages')) +
        ' ' +
        pip_extra_flags +
        ' ' +
        EOL)

    f.write(EOL + '# Download MLC repo for scripts' + EOL)

    if use_copy_repo:
        docker_repo_dest = "$HOME/MLC/repos/mlcommons@mlperf-automations"
        f.write(
            f'COPY --chown=mlcuser:mlc {relative_repo_path} {docker_repo_dest}' +
            EOL)

        f.write(EOL + '# Register MLC repository' + EOL)
        f.write('RUN mlc pull repo --url={} --quiet'.format(docker_repo_dest) + EOL)
        f.write(EOL)

    else:
        # Use mlc pull repo as before
        x = env.get('MLC_DOCKER_ADD_FLAG_TO_MLC_MLOPS_REPO', '')
        if x != '':
            x = ' ' + x

        f.write(
            'RUN mlc pull repo ' +
            mlc_mlops_repo +
            mlc_mlops_repo_branch_string +
            x +
            EOL)

    # Check extra repositories
    x = env.get('MLC_DOCKER_EXTRA_MLC_REPOS', '')
    if x != '':
        for y in x.split(','):
            f.write('RUN ' + y + EOL)

    if not is_true(env.get('MLC_DOCKER_SKIP_MLC_SYS_UPGRADE', False)):
        f.write(EOL + '# Install all system dependencies' + EOL)
        f.write('RUN mlc run script --tags=get,sys-utils-mlc --quiet' + EOL)

    if 'MLC_DOCKER_PRE_RUN_COMMANDS' in env:
        for pre_run_cmd in env['MLC_DOCKER_PRE_RUN_COMMANDS']:
            f.write('RUN ' + pre_run_cmd + EOL)

    run_cmd_extra = " " + \
        env.get('MLC_DOCKER_RUN_CMD_EXTRA', '').replace(":", "=")
    gh_token = get_value(env, config, "GH_TOKEN", "MLC_GH_TOKEN")
    if gh_token:
        run_cmd_extra = " --env.MLC_GH_TOKEN=$MLC_GH_TOKEN"

    f.write(EOL + '# Run commands' + EOL)
    for comment in env.get('MLC_DOCKER_RUN_COMMENTS', []):
        f.write(comment + EOL)

    skip_extra = False
    if 'MLC_DOCKER_RUN_CMD' not in env:
        env['MLC_DOCKER_RUN_CMD'] = ""
        if 'MLC_DOCKER_RUN_SCRIPT_TAGS' not in env:
            env['MLC_DOCKER_RUN_CMD'] += "mlc version"
            skip_extra = True
        else:
            if not is_true(env.get('MLC_DOCKER_NOT_PULL_UPDATE', 'False')):
                env['MLC_DOCKER_RUN_CMD'] += "mlc pull repo && "
            env['MLC_DOCKER_RUN_CMD'] += "mlc run script --tags=" + \
                env['MLC_DOCKER_RUN_SCRIPT_TAGS'] + ' --quiet'
    else:
        if not is_true(env.get('MLC_DOCKER_NOT_PULL_UPDATE', 'False')):
            env['MLC_DOCKER_RUN_CMD'] = "mlc pull repo && " + \
                env['MLC_DOCKER_RUN_CMD']

    logger.info(env['MLC_DOCKER_RUN_CMD'])
    fake_run = env.get("MLC_DOCKER_FAKE_RUN_OPTION",
                       " --fake_run") + dockerfile_env_input_string
    fake_run = fake_run + \
        " --fake_deps" if env.get('MLC_DOCKER_FAKE_DEPS') else fake_run

    x = 'RUN ' + env['MLC_DOCKER_RUN_CMD']

    if not skip_extra:
        x += fake_run
        if '--quiet' not in x:
            x += ' --quiet'
        if run_cmd_extra != '':
            x += ' ' + run_cmd_extra

    if env.get('MLC_DOCKER_RUN_SCRIPT_TAGS', '') != '' and is_true(env.get(
            'MLC_DOCKER_ADD_DEPENDENT_SCRIPTS_RUN_COMMANDS', '')):
        mlc_input = {'action': 'run',
                     'automation': 'script',
                     'tags': f"""{env['MLC_DOCKER_RUN_SCRIPT_TAGS']}""",
                     'print_deps': True,
                     'quiet': True,
                     'silent': True,
                     'fake_run': True,
                     'fake_deps': True
                     }
        r = self_module.mlc.access(mlc_input)
        if r['return'] > 0:
            return r
        print_deps = r['new_state']['print_deps']
        fake_run_str = " --fake_run" if env.get('MLC_DOCKER_FAKE_DEPS') else ""
        cmds = ["RUN " + dep for dep in print_deps]
        for cmd in cmds:
            f.write(cmd + fake_run_str + EOL)

    f.write(x + EOL)

    # fake_run to install the dependent scripts and caching them
    if not "run" in env['MLC_DOCKER_RUN_CMD'] and is_false(
            env.get('MLC_REAL_RUN', False)):
        fake_run = dockerfile_env_input_string

        x = 'RUN ' + env['MLC_DOCKER_RUN_CMD'] + fake_run + run_cmd_extra
        if '--quiet' not in x:
            x += ' --quiet '
        x += EOL

        f.write(x)

    if 'MLC_DOCKER_POST_RUN_COMMANDS' in env:
        for post_run_cmd in env['MLC_DOCKER_POST_RUN_COMMANDS']:
            f.write('RUN ' + post_run_cmd + EOL)

    post_file = env.get('DOCKER_IMAGE_POST_FILE', '')
    if post_file != '':
        r = utils.load_txt(post_file)
        if r['return'] > 0:
            return r

        s = r['string']
        f.write(s + EOL)

    logger.info(f"""Dockerfile written at {dockerfile_with_path}""")

    f.close()

    # f = open(env['MLC_DOCKERFILE_WITH_PATH'], "r")
    # print(f.read())

    return {'return': 0}


def get_value(env, config, key, env_key=None):
    if not env_key:
        env_key = key

    if env.get(env_key, None) is not None:
        return env[env_key]

    docker_os = env['MLC_DOCKER_OS']
    docker_os_version = env['MLC_DOCKER_OS_VERSION']

    version_meta = config['distros'][docker_os]['versions'].get(
        docker_os_version, '')
    if key in version_meta:
        return version_meta[key]

    distro_meta = config['distros'][docker_os]
    if key in distro_meta:
        return distro_meta[key]

    if key in config:
        return config[key]

    return None
