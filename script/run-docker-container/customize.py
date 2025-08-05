from mlc import utils
import os
import subprocess
from os.path import exists
import json
from utils import *


def preprocess(i):

    os_info = i['os_info']

    env = i['env']

    mlc = i['automation'].action_object

    logger = i['automation'].logger

    interactive = env.get('MLC_DOCKER_INTERACTIVE_MODE', '')

    if is_true(interactive):
        env['MLC_DOCKER_DETACHED_MODE'] = 'no'

    if 'MLC_DOCKER_RUN_SCRIPT_TAGS' not in env:
        env['MLC_DOCKER_RUN_SCRIPT_TAGS'] = "run,docker,container"
        MLC_RUN_CMD = "mlc version"
    else:
        MLC_RUN_CMD = "mlcr " + \
            env['MLC_DOCKER_RUN_SCRIPT_TAGS'] + ' --quiet'

    r = mlc.access({'action': 'search',
                   'automation': 'script',
                    'tags': env['MLC_DOCKER_RUN_SCRIPT_TAGS']})
    if len(r['list']) < 1:
        raise Exception(
            'MLC script with tags ' +
            env['MLC_DOCKER_RUN_SCRIPT_TAGS'] +
            ' not found!')

    PATH = r['list'][0].path
    os.chdir(PATH)

    env['MLC_DOCKER_RUN_CMD'] = MLC_RUN_CMD

    # Updating Docker info
    update_docker_info(env)

    docker_image_repo = env['MLC_DOCKER_IMAGE_REPO']
    docker_image_base = env['MLC_DOCKER_IMAGE_BASE']
    docker_image_name = env['MLC_DOCKER_IMAGE_NAME']
    docker_image_tag = env['MLC_DOCKER_IMAGE_TAG']

    DOCKER_CONTAINER = docker_image_repo + "/" + \
        docker_image_name + ":" + docker_image_tag

    logger.info('')
    logger.info('Checking existing Docker container:')
    logger.info('')
    # CMD = f"""{env['MLC_CONTAINER_TOOL']} ps --format=json  --filter "ancestor={DOCKER_CONTAINER}" """
    CMD = f"""{env['MLC_CONTAINER_TOOL']} ps --format """ + \
        '"{{ .ID }},"' + f"""  --filter "ancestor={DOCKER_CONTAINER}" """
    if os_info['platform'] == 'windows':
        CMD += " 2> nul"
    else:
        CMD += " 2> /dev/null || true "

    logger.info('  ' + CMD)
    logger.info('')

    try:
        out = subprocess.check_output(
            CMD, shell=True, text=True).strip()
    except Exception as e:
        return {
            'return': 1,
            'error': 'Unexpected error occurred with docker run:\n{}'.format(e)
        }

    existing_container_id = None
    if len(out) > 0:
        out_split = out.split(",")
        if len(out_split) > 0:
            existing_container_id = out_split[0].strip()

    if existing_container_id and is_true(
            env.get('MLC_DOCKER_REUSE_EXISTING_CONTAINER', '')):
        logger.info(f"Reusing existing container {existing_container_id}")
        env['MLC_DOCKER_CONTAINER_ID'] = existing_container_id

    else:
        if existing_container_id:
            print(
                f"""Not using existing container {existing_container_id} as env['MLC_DOCKER_REUSE_EXISTING_CONTAINER'] is not set""")
        else:
            logger.info("No existing container")
        if env.get('MLC_DOCKER_CONTAINER_ID', '') != '':
            del (env['MLC_DOCKER_CONTAINER_ID'])  # not valid ID

        CMD = f"""{env['MLC_CONTAINER_TOOL']} images -q """ + DOCKER_CONTAINER

        if os_info['platform'] == 'windows':
            CMD += " 2> nul"
        else:
            CMD += " 2> /dev/null || true"

        logger.info('')
        logger.info('Checking Docker images:')
        logger.info('')
        logger.info('  ' + CMD)
        logger.info('')

        try:
            docker_image = subprocess.check_output(
                CMD, shell=True).decode("utf-8")
        except Exception as e:
            return {
                'return': 1, 'error': 'Docker is either not installed or not started:\n{}'.format(e)}

        recreate_image = env.get('MLC_DOCKER_IMAGE_RECREATE', '')

        if is_false(recreate_image):
            if docker_image:
                logger.info("Docker image exists with ID: " + docker_image)
                env['MLC_DOCKER_IMAGE_EXISTS'] = "yes"

    #    elif recreate_image == "yes":
    #        env['MLC_DOCKER_IMAGE_RECREATE'] = "no"
    return {'return': 0}


def postprocess(i):

    os_info = i['os_info']

    env = i['env']

    logger = i['automation'].logger

    # Updating Docker info
    update_docker_info(env)

    docker_image_repo = env['MLC_DOCKER_IMAGE_REPO']
    docker_image_base = env['MLC_DOCKER_IMAGE_BASE']
    docker_image_name = env['MLC_DOCKER_IMAGE_NAME']
    docker_image_tag = env['MLC_DOCKER_IMAGE_TAG']

    run_cmds = []
    mount_cmds = []
    port_map_cmds = []
    run_opts = ''

    # not completed as su command breaks the execution sequence
    #
    # if env.get('MLC_DOCKER_PASS_USER_ID', '') != '':
    #    run_opts += " --user 0 "
    #    run_cmds.append(f"(usermod -u {os.getuid()} cmuser || echo pass)")
    #    run_cmds.append(f"(chown -R {os.getuid()}:{os.getuid()} /home/cmuser  || echo pass)")
    #    run_cmds.append(" ( su cmuser )")
    #    run_cmds.append('export PATH="/home/cmuser/venv/cm/bin:$PATH"')

    if env.get('MLC_DOCKER_PRE_RUN_COMMANDS', []):
        for pre_run_cmd in env['MLC_DOCKER_PRE_RUN_COMMANDS']:
            run_cmds.append(pre_run_cmd)

    if env.get('MLC_DOCKER_VOLUME_MOUNTS', []):
        for mounts in env['MLC_DOCKER_VOLUME_MOUNTS']:
            mount_cmds.append(mounts)

    if env.get('MLC_DOCKER_PASS_USER_GROUP',
               '') != '' and os_info['platform'] != 'windows':
        run_opts += " --group-add $(id -g $USER) "

    if env.get('MLC_DOCKER_ADD_DEVICE', '') != '':
        run_opts += " --device=" + env['MLC_DOCKER_ADD_DEVICE']

    if is_true(env.get('MLC_DOCKER_PRIVILEGED_MODE', '')):
        run_opts += " --privileged "

    if env.get('MLC_DOCKER_ADD_NUM_GPUS', '') != '':
        run_opts += " --gpus={}".format(env['MLC_DOCKER_ADD_NUM_GPUS'])
    elif env.get('MLC_DOCKER_ADD_ALL_GPUS', '') != '':
        run_opts += " --gpus=all"

    if env.get('MLC_DOCKER_SHM_SIZE', '') != '':
        run_opts += " --shm-size={}".format(env['MLC_DOCKER_SHM_SIZE'])

    if env.get('MLC_DOCKER_EXTRA_RUN_ARGS', '') != '':
        run_opts += env['MLC_DOCKER_EXTRA_RUN_ARGS']

    if is_true(env.get('MLC_DOCKER_USE_GOOGLE_DNS', '')):
        run_opts += ' --dns 8.8.8.8 --dns 8.8.4.4 '

    if env.get('MLC_CONTAINER_TOOL', '') == 'podman' and not is_false(env.get(
            'MLC_PODMAN_MAP_USER_ID', '')):
        run_opts += " --userns=keep-id"

    if env.get('MLC_DOCKER_PORT_MAPS', []):
        for ports in env['MLC_DOCKER_PORT_MAPS']:
            port_map_cmds.append(ports)

    run_cmd = env['MLC_DOCKER_RUN_CMD'] + " " + \
        env.get('MLC_DOCKER_RUN_CMD_EXTRA', '').replace(":", "=")
    run_cmds.append(run_cmd)
    if 'MLC_DOCKER_POST_RUN_COMMANDS' in env:
        for post_run_cmd in env['MLC_DOCKER_POST_RUN_COMMANDS']:
            run_cmds.append(post_run_cmd)

    run_cmd = " && ".join(run_cmds)
    run_cmd = run_cmd.replace("--docker_run_deps", "")

    if mount_cmds:
        for i, mount_cmd in enumerate(mount_cmds):

            # Since windows may have 2 :, we search from the right
            j = mount_cmd.rfind(':')
            if j > 0:
                mount_parts = [mount_cmd[:j], mount_cmd[j + 1:]]
            else:
                return {'return': 1, 'error': 'Can\'t find separator : in a mount string: {}'.format(
                    mount_cmd)}

            host_mount = mount_parts[0]

            if not os.path.exists(host_mount):
                os.makedirs(host_mount)

            abs_host_mount = os.path.abspath(mount_parts[0])

            if abs_host_mount != host_mount or " " in abs_host_mount and not host_mount.startswith(
                    '"'):
                mount_cmds[i] = f"\"{abs_host_mount}\":{mount_parts[1]}"

        mount_cmd_string = " -v " + " -v ".join(mount_cmds)
    else:
        mount_cmd_string = ''
    run_opts += mount_cmd_string

    if port_map_cmds:
        port_map_cmd_string = " -p " + "-p ".join(port_map_cmds)
    else:
        port_map_cmd_string = ''

    run_opts += port_map_cmd_string

    # Currently have problem running Docker in detached mode on Windows:
    detached = is_true(env.get('MLC_DOCKER_DETACHED_MODE', ''))

#    if detached and os_info['platform'] != 'windows':
    if detached:
        if os_info['platform'] == 'windows':
            return {
                'return': 1, 'error': 'Currently we don\'t support running Docker containers in detached mode on Windows - TBD'}

        existing_container_id = env.get('MLC_DOCKER_CONTAINER_ID', '')
        if existing_container_id:
            CMD = f"""ID={existing_container_id} && {env['MLC_CONTAINER_TOOL']} exec $ID bash -c '""" + run_cmd + "'"
        else:
            CONTAINER = f"""{env['MLC_CONTAINER_TOOL']} run -dt {run_opts} --rm  {docker_image_repo}/{docker_image_name}:{docker_image_tag} bash"""
            CMD = f"""ID=`{CONTAINER}` && {env['MLC_CONTAINER_TOOL']} exec $ID bash -c '{run_cmd}'"""

            if is_true(env.get('MLC_KILL_DETACHED_CONTAINER', False)):
                CMD += f""" && {env['MLC_CONTAINER_TOOL']} kill $ID >/dev/null"""

        CMD += ' && echo "ID=$ID"'

        logger.info('=========================')
        logger.info("Container launch command:")
        logger.info('')
        logger.info(f"{CMD}")
        logger.info('')
        print(
            "Running " +
            run_cmd +
            f""" inside {env['MLC_CONTAINER_TOOL']} container""")

        record_script({'cmd': CMD, 'env': env})

        logger.info('')
        # Execute the command
        try:
            result = subprocess.run(
                CMD,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True)
            logger.info("Command Output:", result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error("Error Occurred!")
            logger.info(f"Command: {e.cmd}")
            logger.info(f"Return Code: {e.returncode}")
            logger.error(f"Error Output: {e.stderr}")
            return {'return': 1, 'error': e.stderr}

        docker_out = result.stdout
        # if docker_out != 0:
        # return {'return': docker_out, 'error': f""{env['MLC_CONTAINER_TOOL']}
        # run failed""}

        lines = docker_out.split("\n")

        for line in lines:
            if line.startswith("ID="):
                ID = line[3:]
                env['MLC_DOCKER_CONTAINER_ID'] = ID

        logger.info(f"{docker_out}")

    else:
        x = "'"
        if os_info['platform'] == 'windows':
            x = '"'

        x1 = ''
        x2 = ''
        run_cmd_prefix = ""
        if is_true(env.get('MLC_DOCKER_INTERACTIVE_MODE', '')):
            run_cmd_prefix = "("
            x1 = '-it'
            x2 = " && bash ) || bash"

        CONTAINER = f"{env['MLC_CONTAINER_TOOL']} run " + x1 + " --entrypoint " + x + x + " " + run_opts + \
            " " + docker_image_repo + "/" + docker_image_name + ":" + docker_image_tag
        CMD = CONTAINER + " bash -c " + x + run_cmd_prefix + run_cmd + x2 + x

        logger.info('')
        logger.info("Container launch command:")
        logger.info('')
        logger.info(f"{CMD}")

        record_script({'cmd': CMD, 'env': env})

        logger.info('')
        docker_out = os.system(CMD)
        if docker_out != 0:
            if docker_out % 256 == 0:
                docker_out = 1
            return {'return': docker_out,
                    'error': f"""{env['MLC_CONTAINER_TOOL']} run failed"""}

    return {'return': 0}


def record_script(i):

    cmd = i['cmd']
    env = i['env']

    files = []

    dockerfile_path = env.get('MLC_DOCKERFILE_WITH_PATH', '')
    if dockerfile_path != '' and os.path.isfile(dockerfile_path):
        files.append(dockerfile_path + '.run.bat')
        files.append(dockerfile_path + '.run.sh')

    save_script = env.get('MLC_DOCKER_SAVE_SCRIPT', '')
    if save_script != '':
        if save_script.endswith('.bat') or save_script.endswith('.sh'):
            files.append(save_script)
        else:
            files.append(save_script + '.bat')
            files.append(save_script + '.sh')

    for filename in files:
        with open(filename, 'w') as f:
            f.write(cmd + '\n')

    return {'return': 0}


def update_docker_info(env):

    # Updating Docker info
    docker_image_repo = env.get('MLC_DOCKER_IMAGE_REPO', 'localhost/local')
    env['MLC_DOCKER_IMAGE_REPO'] = docker_image_repo

    docker_image_base = env.get('MLC_DOCKER_IMAGE_BASE')
    if not docker_image_base:
        if env.get("MLC_DOCKER_OS", '') != '':
            docker_image_base = env["MLC_DOCKER_OS"] + \
                ":" + env["MLC_DOCKER_OS_VERSION"]
        else:
            docker_image_base = "ubuntu:22.04"

    env['MLC_DOCKER_IMAGE_BASE'] = docker_image_base

    if env.get('MLC_DOCKER_IMAGE_NAME', '') != '':
        docker_image_name = env['MLC_DOCKER_IMAGE_NAME']
    else:
        docker_image_name = 'mlc-script-' + \
            env['MLC_DOCKER_RUN_SCRIPT_TAGS'].replace(
                ',', '-').replace('_', '-').replace('+', 'plus')
        env['MLC_DOCKER_IMAGE_NAME'] = docker_image_name

    docker_image_tag_extra = env.get('MLC_DOCKER_IMAGE_TAG_EXTRA', '-latest')

    docker_image_tag = env.get('MLC_DOCKER_IMAGE_TAG', docker_image_base.replace(
        ':', '-').replace('_', '').replace("/", "-") + docker_image_tag_extra)
    env['MLC_DOCKER_IMAGE_TAG'] = docker_image_tag

    return
