from mlc import utils
import os
from os.path import exists
from utils import *


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger
    dockerfile_path = env.get('MLC_DOCKERFILE_WITH_PATH', '')
    if dockerfile_path != '' and os.path.exists(dockerfile_path):
        build_dockerfile = False
        env['MLC_BUILD_DOCKERFILE'] = "no"
        os.chdir(os.path.dirname(dockerfile_path))
    else:
        build_dockerfile = True
        env['MLC_BUILD_DOCKERFILE'] = "yes"
        env['MLC_DOCKERFILE_BUILD_FROM_IMAGE_SCRIPT'] = "yes"

    MLC_DOCKER_BUILD_ARGS = env.get('+ MLC_DOCKER_BUILD_ARGS', [])


    if not is_false(env.get('MLC_DOCKER_USE_HOST_USER_ID')) and os.name != 'nt' and "UID=\" $(id -u $USER) \"" not in MLC_DOCKER_BUILD_ARGS:
        MLC_DOCKER_BUILD_ARGS.append(f"UID=\" $(id -u $USER) \"")
    if not is_false(env.get('MLC_DOCKER_USE_HOST_GROUP_ID')) and os.name != 'nt' and "GID=\" $(id -g $USER) \"" not in MLC_DOCKER_BUILD_ARGS:
        MLC_DOCKER_BUILD_ARGS.append(f"GID=\" $(id -g $USER) \"")

    if env.get('MLC_GH_TOKEN', '') != '':
        MLC_DOCKER_BUILD_ARGS.append("MLC_GH_TOKEN=" + env['MLC_GH_TOKEN'])

    if MLC_DOCKER_BUILD_ARGS:
        build_args = "--build-arg " + \
            " --build-arg ".join(MLC_DOCKER_BUILD_ARGS)
    else:
        build_args = ""

    env['MLC_DOCKER_BUILD_ARGS'] = build_args

#    if 'MLC_DOCKERFILE_WITH_PATH' not in env or not exists(env['MLC_DOCKERFILE_WITH_PATH']):
#        env['MLC_BUILD_DOCKERFILE'] = "yes"
#    else:
#        env['MLC_BUILD_DOCKERFILE'] = "no"
#
    if env.get("MLC_DOCKER_IMAGE_REPO", "") == '':
        env['MLC_DOCKER_IMAGE_REPO'] = "localhost/local"

    docker_image_name = env.get('MLC_DOCKER_IMAGE_NAME', '')
    if docker_image_name == '':
        docker_image_name = "mlc-script-" + \
            env.get('MLC_DOCKER_RUN_SCRIPT_TAGS', '').replace(
                ',', '-').replace('_', '-')

    env['MLC_DOCKER_IMAGE_NAME'] = docker_image_name.lower()

    if env.get("MLC_DOCKER_IMAGE_TAG", "") == '':
        env['MLC_DOCKER_IMAGE_TAG'] = "latest"

    if is_false(env.get("MLC_DOCKER_CACHE", "True")):
        env["MLC_DOCKER_CACHE_ARG"] = " --no-cache"

    CMD = ''

    image_name = get_image_name(env)

    if build_dockerfile:
        dockerfile_path = r"\${MLC_DOCKERFILE_WITH_PATH}"

    # Write .dockerignore
    with open('.dockerignore', 'w') as f:
        f.write('.git\n')

    # Prepare CMD to build image
    XCMD = [
        f'{env["MLC_CONTAINER_TOOL"]} build ' +
        env.get('MLC_DOCKER_CACHE_ARG', ''),
        ' ' + build_args,
        ' -f "' + dockerfile_path + '"',
        ' -t "' + image_name,
        ' .'
    ]

    with open(dockerfile_path + '.build.sh', 'w') as f:
        f.write(' \\\n'.join(XCMD) + '\n')

    with open(dockerfile_path + '.build.bat', 'w') as f:
        f.write(' ^\n'.join(XCMD) + '\n')

    CMD = ''.join(XCMD)

    logger.info(CMD)

    env['MLC_DOCKER_BUILD_CMD'] = CMD

    return {'return': 0}


def get_image_name(env):

    image_name = env.get('MLC_DOCKER_IMAGE_REPO', '') + '/' + \
        env.get('MLC_DOCKER_IMAGE_NAME', '') + ':' + \
        env.get('MLC_DOCKER_IMAGE_TAG', '') + '"'

    return image_name


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger

    # Check if need to push docker image to the Docker Hub
    if is_true(env.get('MLC_DOCKER_PUSH_IMAGE', '')):
        image_name = get_image_name(env)

        # Prepare CMD to build image
        PCMD = 'docker image push ' + image_name

        dockerfile_path = env.get('MLC_DOCKERFILE_WITH_PATH', '')
        if dockerfile_path != '' and os.path.isfile(dockerfile_path):
            with open(dockerfile_path + '.push.sh', 'w') as f:
                f.write(PCMD + '\n')

            with open(dockerfile_path + '.build.bat', 'w') as f:
                f.write(PCMD + '\n')

        logger.info(PCMD)

        logger.info('')

        r = os.system(PCMD)
        logger.info('')

        if r > 0:
            return {'return': 1, 'error': 'pushing to Docker Hub failed'}

    return {'return': 0}
