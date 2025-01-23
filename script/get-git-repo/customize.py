from mlc import utils
import os
import shutil


def preprocess(i):

    os_info = i['os_info']

#    if os_info['platform'] == 'windows':
# return {'return':1, 'error': 'Windows is not supported in this script
# yet'}

    env = i['env']
    meta = i['meta']

    env_key = get_env_key(env)

    cm_git_url = env['MLC_GIT_URL']

    if 'MLC_GIT_REPO_NAME' not in env:
        update_env(
            env,
            'MLC_GIT_REPO{}_NAME',
            env_key,
            os.path.basename(
                env['MLC_GIT_URL']))

    if 'MLC_GIT_DEPTH' not in env:
        env['MLC_GIT_DEPTH'] = ''

    if 'MLC_GIT_RECURSE_SUBMODULES' not in env:
        env['MLC_GIT_RECURSE_SUBMODULES'] = ''

    if env.get('MLC_GIT_CHECKOUT', '') == '':
        env['MLC_GIT_CHECKOUT'] = env.get(
            'MLC_GIT_SHA', env.get(
                'MLC_GIT_BRANCH', ''))

    git_checkout_string = " -b " + env['MLC_GIT_BRANCH'] if (
        "MLC_GIT_BRANCH" in env and env.get('MLC_GIT_SHA', '') == '') else ""

    git_clone_cmd = "git clone " + env['MLC_GIT_RECURSE_SUBMODULES'] + git_checkout_string + " " + \
        env['MLC_GIT_URL'] + " " + \
        env.get('MLC_GIT_DEPTH', '') + ' ' + env['MLC_GIT_CHECKOUT_FOLDER']

    env['MLC_GIT_CLONE_CMD'] = git_clone_cmd
    env['MLC_TMP_GIT_PATH'] = os.path.join(
        os.getcwd(), env['MLC_GIT_CHECKOUT_FOLDER'], ".gitdone")

    return {'return': 0}


def postprocess(i):

    env = i['env']
    state = i['state']
    env['MLC_GIT_CHECKOUT_PATH'] = os.path.join(
        os.getcwd(), env['MLC_GIT_CHECKOUT_FOLDER'])
    git_checkout_path = env['MLC_GIT_CHECKOUT_PATH']

    env_key = get_env_key(env)

    # We remap MLC_GIT variables with MLC_GIT_REPO prefix so that they don't
    # contaminate the env of the parent script
    update_env(env, 'MLC_GIT_REPO{}_CHECKOUT_PATH',
               env_key, env['MLC_GIT_CHECKOUT_PATH'])
    update_env(env, 'MLC_GIT_REPO{}_URL', env_key, env['MLC_GIT_URL'])
    update_env(
        env,
        'MLC_GIT_REPO{}_CHECKOUT',
        env_key,
        env['MLC_GIT_CHECKOUT'])
    update_env(env, 'MLC_GIT_REPO{}_DEPTH', env_key, env['MLC_GIT_DEPTH'])
    update_env(env, 'MLC_GIT_REPO{}_CHECKOUT_FOLDER',
               env_key, env['MLC_GIT_CHECKOUT_FOLDER'])
    update_env(env, 'MLC_GIT_REPO{}_PATCH', env_key, env['MLC_GIT_PATCH'])
    update_env(env, 'MLC_GIT_REPO{}_RECURSE_SUBMODULES',
               env_key, env['MLC_GIT_RECURSE_SUBMODULES'])

    if (env.get('MLC_GIT_CHECKOUT_PATH_ENV_NAME', '') != ''):
        env[env['MLC_GIT_CHECKOUT_PATH_ENV_NAME']] = git_checkout_path

    env['MLC_GET_DEPENDENT_CACHED_PATH'] = git_checkout_path

    if os.path.exists("tmp-mlc-git-hash.out"):
        with open("tmp-mlc-git-hash.out", "r") as f:
            git_hash = f.readline().strip()
            env['MLC_GIT_REPO_CURRENT_HASH'] = git_hash

    return {'return': 0}


def get_env_key(env):

    env_key = env.get('MLC_GIT_ENV_KEY', '')

    if env_key != '' and not env_key.startswith('_'):
        env_key = '_' + env_key

    return env_key


def update_env(env, key, env_key, var):

    env[key.format('')] = var

    if env_key != '':
        env[key.format(env_key)] = var

    return
