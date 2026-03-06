from mlc import utils
import os
import shutil
from datetime import datetime
import re


def preprocess(i):

    os_info = i['os_info']

    env = i['env']
    meta = i['meta']

    env_key = get_env_key(env)

    mlc_git_url = env['MLC_GIT_URL']

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

    version_string = generate_src_version_string(env)
    env['MLC_GIT_REPO_VERSION_STRING'] = version_string

    if (env.get('MLC_GIT_REPO_VERSION_ENV_NAME', '') != ''):
        env[env['MLC_GIT_REPO_VERSION_ENV_NAME']] = version_string

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


def generate_src_version_string(env):
    """
    Generates a descriptive version string including checkout state,
    date, short hash, and modifiers (PRs, cherry-picks, patches).
    """

    # 1. Base Components
    checkout = env.get("MLC_GIT_CHECKOUT", "unknown")
    sha = env.get("MLC_GIT_SHA", "00000000")

    # Generate the date string (e.g., 20260224)
    # This uses the current build/checkout date.
    date_str = datetime.now().strftime("%Y%m%d")

    # Sanitize checkout string (e.g., "feature/login" -> "feature-login")
    safe_checkout = re.sub(r'[^a-zA-Z0-9]', '-', checkout).strip('-').lower()
    short_sha = sha[:8]

    # Start building the string parts: Branch + Date + Hash
    version_parts = [f"{safe_checkout}-{date_str}-g{short_sha}"]

    # 2. Add Pull Request info
    pr = env.get("MLC_GIT_APPLIED_PR")
    if pr:
        # Extract just the numbers from the PR string
        pr_num = re.search(r'\d+', pr)
        pr_str = pr_num.group(0) if pr_num else "pr"
        version_parts.append(f"pr{pr_str}")

    # 3. Add Cherry-pick info
    cps = env.get("MLC_GIT_APPLIED_CHERRYPICKS")
    if cps:
        cp_list = [cp for cp in cps.split(';') if cp.strip()]
        if cp_list:
            version_parts.append(f"cp{len(cp_list)}")

    # 4. Add Patch info
    patches = env.get("MLC_GIT_APPLIED_PATCHES")
    if patches:
        patch_list = [p for p in patches.split(';') if p.strip()]
        if patch_list:
            version_parts.append(f"p{len(patch_list)}")

    # Assemble the final string
    return "-".join(version_parts)
