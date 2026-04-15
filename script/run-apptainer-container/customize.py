from mlc import utils
import os
import subprocess
from utils import *


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    mlc = i['automation'].action_object
    logger = i['automation'].logger

    if os_info['platform'] == 'windows':
        return {
            'return': 1,
            'error': 'Apptainer is not natively supported on Windows. '
                     'Please use WSL2 or a Linux VM.'}

    if 'MLC_APPTAINER_RUN_SCRIPT_TAGS' not in env:
        env['MLC_APPTAINER_RUN_SCRIPT_TAGS'] = "run,apptainer,container"
        MLC_RUN_CMD = "mlc --help"
    else:
        MLC_RUN_CMD = "mlcr " + \
            env['MLC_APPTAINER_RUN_SCRIPT_TAGS'] + ' --quiet'

    env['MLC_APPTAINER_RUN_CMD'] = MLC_RUN_CMD

    # Compute image naming (like run-docker-container's update_docker_info)
    update_apptainer_info(env)

    sif_path = env['MLC_APPTAINER_SIF_PATH']

    # Check if SIF image already exists
    recreate_image = env.get('MLC_APPTAINER_IMAGE_RECREATE', '')

    if not is_true(recreate_image) and os.path.exists(sif_path):
        logger.info('')
        logger.info(f'Apptainer SIF image exists: {sif_path}')
        env['MLC_APPTAINER_IMAGE_EXISTS'] = 'yes'
    else:
        logger.info('')
        logger.info(f'Apptainer SIF image not found: {sif_path}')
        logger.info('Will build via build-apptainer-image -> build-apptainerfile')

    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger

    # Re-compute in case build step updated things
    update_apptainer_info(env)

    sif_path = env['MLC_APPTAINER_SIF_PATH']

    if not os.path.exists(sif_path):
        return {
            'return': 1,
            'error': f'Apptainer SIF image not found after build: {sif_path}'}

    run_cmds = []
    run_opts = ''

    # GPU support
    if is_true(env.get('MLC_APPTAINER_NV', '')):
        run_opts += ' --nv'

    if is_true(env.get('MLC_APPTAINER_ROCM', '')):
        run_opts += ' --rocm'

    # Filesystem options
    if is_true(env.get('MLC_APPTAINER_WRITABLE', '')):
        run_opts += ' --writable'
    elif is_true(env.get('MLC_APPTAINER_WRITABLE_TMPFS', '')):
        run_opts += ' --writable-tmpfs'

    # Environment isolation
    if is_true(env.get('MLC_APPTAINER_CLEANENV', '')):
        run_opts += ' --cleanenv'

    if is_true(env.get('MLC_APPTAINER_CONTAIN', '')):
        run_opts += ' --contain'

    if is_true(env.get('MLC_APPTAINER_CONTAINALL', '')):
        run_opts += ' --containall'

    if is_true(env.get('MLC_APPTAINER_NO_HOME', '')):
        run_opts += ' --no-home'

    if is_true(env.get('MLC_APPTAINER_FAKEROOT', '')):
        run_opts += ' --fakeroot'

    # Home directory
    if env.get('MLC_APPTAINER_HOME', '') != '':
        run_opts += f" --home {env['MLC_APPTAINER_HOME']}"

    # Working directory
    if env.get('MLC_APPTAINER_PWD', '') != '':
        run_opts += f" --pwd {env['MLC_APPTAINER_PWD']}"

    # Bind mounts
    if env.get('MLC_APPTAINER_BIND_MOUNTS', []):
        for mount in env['MLC_APPTAINER_BIND_MOUNTS']:
            run_opts += f' --bind {mount}'

    # Overlay
    if env.get('MLC_APPTAINER_OVERLAY', '') != '':
        run_opts += f" --overlay {env['MLC_APPTAINER_OVERLAY']}"

    # Environment variables to pass into the container
    if env.get('MLC_APPTAINER_ENV_VARS', []):
        for evar in env['MLC_APPTAINER_ENV_VARS']:
            run_opts += f' --env {evar}'

    # Extra user args
    if env.get('MLC_APPTAINER_EXTRA_ARGS', '') != '':
        run_opts += ' ' + env['MLC_APPTAINER_EXTRA_ARGS']

    # Pre-run commands
    if env.get('MLC_APPTAINER_PRE_RUN_COMMANDS', []):
        for pre_cmd in env['MLC_APPTAINER_PRE_RUN_COMMANDS']:
            run_cmds.append(pre_cmd)

    # Main run command — activate the venv first, then run the MLC command
    run_cmd = env['MLC_APPTAINER_RUN_CMD'] + ' ' + \
        env.get('MLC_APPTAINER_RUN_CMD_EXTRA', '').replace(':', '=')
    run_cmds.append(run_cmd)

    # Post-run commands
    if env.get('MLC_APPTAINER_POST_RUN_COMMANDS', []):
        for post_cmd in env['MLC_APPTAINER_POST_RUN_COMMANDS']:
            run_cmds.append(post_cmd)

    run_cmd_combined = ' && '.join(run_cmds)

    # Activate venv inside the container before running commands
    full_cmd = f". /opt/venv/mlcflow/bin/activate && {run_cmd_combined}"

    CMD = f"apptainer exec{run_opts} {sif_path} bash -c '{full_cmd}'"

    logger.info('')
    logger.info('Apptainer launch command:')
    logger.info('')
    logger.info(f'  {CMD}')
    logger.info('')

    record_script({'cmd': CMD, 'env': env})

    ret = os.system(CMD)
    if ret != 0:
        if ret % 256 == 0:
            ret = 1
        return {'return': ret, 'error': 'apptainer exec failed'}

    return {'return': 0}


def update_apptainer_info(env):
    """Compute SIF image path and naming from env, similar to Docker's update_docker_info."""

    apptainer_os = env.get('MLC_APPTAINER_OS', 'ubuntu')
    apptainer_os_version = env.get('MLC_APPTAINER_OS_VERSION', '24.04')
    env['MLC_APPTAINER_OS'] = apptainer_os
    env['MLC_APPTAINER_OS_VERSION'] = apptainer_os_version

    image_name = env.get('MLC_APPTAINER_IMAGE_NAME', '')
    if image_name == '':
        image_name = 'mlc-script-' + \
            env.get('MLC_APPTAINER_RUN_SCRIPT_TAGS', 'default').replace(
                ',', '-').replace('_', '-').replace('+', 'plus')
    env['MLC_APPTAINER_IMAGE_NAME'] = image_name.lower()

    image_tag = env.get('MLC_APPTAINER_IMAGE_TAG', '')
    if image_tag == '':
        image_tag = f"{apptainer_os}-{apptainer_os_version}-latest"
    env['MLC_APPTAINER_IMAGE_TAG'] = image_tag

    # If user provided a direct image/SIF path, use it
    direct_image = env.get('MLC_APPTAINER_IMAGE', '').strip()
    if direct_image:
        env['MLC_APPTAINER_SIF_PATH'] = direct_image
        env['MLC_APPTAINER_SKIP_BUILD'] = 'yes'
        return

    # If user provided a URL, use it directly
    image_url = env.get('MLC_APPTAINER_IMAGE_URL', '').strip()
    if image_url:
        env['MLC_APPTAINER_SIF_PATH'] = image_url
        env['MLC_APPTAINER_SKIP_BUILD'] = 'yes'
        return

    # Standard SIF naming: build from definition file
    sif_name = f"{env['MLC_APPTAINER_IMAGE_NAME']}_{image_tag}.sif"
    env['MLC_APPTAINER_SIF_PATH'] = os.path.join(os.getcwd(), sif_name)


def record_script(i):
    cmd = i['cmd']
    env = i['env']

    save_script = env.get('MLC_APPTAINER_SAVE_SCRIPT', '')
    if save_script == '':
        return {'return': 0}

    files = []
    if save_script.endswith('.sh'):
        files.append(save_script)
    else:
        files.append(save_script + '.sh')

    for filename in files:
        with open(filename, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write(cmd + '\n')

    return {'return': 0}
