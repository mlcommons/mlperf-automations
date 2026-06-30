from mlc import utils
import os
import shutil


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger
    script_dir = i['run_script_input']['path']
    cache_dir = os.getcwd()

    env['MLC_ANSIBLE_RUN_DIR'] = cache_dir

    # Install galaxy requirements if specified
    galaxy_requirements = env.get('MLC_ANSIBLE_GALAXY_REQUIREMENTS', '')
    if galaxy_requirements and os.path.isfile(galaxy_requirements):
        env['MLC_ANSIBLE_GALAXY_INSTALL_CMD'] = f'ansible-galaxy install -r {galaxy_requirements}'
    else:
        env['MLC_ANSIBLE_GALAXY_INSTALL_CMD'] = ''

    # Resolve playbook path
    playbook = env.get('MLC_ANSIBLE_PLAYBOOK', '')
    if not playbook:
        return {'return': 1,
                'error': 'Please specify --playbook=<path_to_playbook.yml>'}

    if not os.path.isabs(playbook):
        # Check relative to script dir first, then current dir
        if os.path.isfile(os.path.join(script_dir, playbook)):
            playbook = os.path.join(script_dir, playbook)
        elif not os.path.isfile(playbook):
            return {'return': 1, 'error': f'Playbook not found: {playbook}'}

    env['MLC_ANSIBLE_PLAYBOOK_PATH'] = playbook

    # Build ansible-playbook command arguments
    ansible_args = []

    # Inventory
    inventory = env.get('MLC_ANSIBLE_INVENTORY', '')
    if inventory:
        if not os.path.isabs(inventory):
            if os.path.isfile(os.path.join(script_dir, inventory)):
                inventory = os.path.join(script_dir, inventory)
        ansible_args.append(f'-i {inventory}')

    # Extra variables
    extra_vars = env.get('MLC_ANSIBLE_EXTRA_VARS', '')
    if extra_vars:
        ansible_args.append(f'--extra-vars "{extra_vars}"')

    # Limit hosts
    limit = env.get('MLC_ANSIBLE_LIMIT', '')
    if limit:
        ansible_args.append(f'--limit {limit}')

    # Tags
    ansible_tags = env.get('MLC_ANSIBLE_TAGS', '')
    if ansible_tags:
        ansible_args.append(f'--tags {ansible_tags}')

    # Skip tags
    skip_tags = env.get('MLC_ANSIBLE_SKIP_TAGS', '')
    if skip_tags:
        ansible_args.append(f'--skip-tags {skip_tags}')

    # Forks
    forks = env.get('MLC_ANSIBLE_FORKS', '5')
    ansible_args.append(f'--forks {forks}')

    # Verbosity
    verbosity = env.get('MLC_ANSIBLE_VERBOSITY', '')
    if verbosity:
        ansible_args.append(f'-{verbosity}')

    # Private key
    private_key = env.get('MLC_ANSIBLE_PRIVATE_KEY', '')
    if private_key:
        ansible_args.append(f'--private-key {private_key}')

    # Remote user
    user = env.get('MLC_ANSIBLE_USER', '')
    if user:
        ansible_args.append(f'--user {user}')

    # Become (sudo)
    become = env.get('MLC_ANSIBLE_BECOME', '')
    if become:
        ansible_args.append('--become')

    # Vault password file
    vault_password_file = env.get('MLC_ANSIBLE_VAULT_PASSWORD_FILE', '')
    if vault_password_file:
        ansible_args.append(f'--vault-password-file {vault_password_file}')

    # Ansible config file
    config_file = env.get('MLC_ANSIBLE_CONFIG_FILE', '')
    if config_file:
        env['ANSIBLE_CONFIG'] = config_file

    # Roles path
    roles_path = env.get('MLC_ANSIBLE_ROLES_PATH', '')
    if roles_path:
        env['ANSIBLE_ROLES_PATH'] = roles_path

    env['MLC_ANSIBLE_ARGS'] = ' '.join(ansible_args)

    logger.info(f"Running ansible-playbook from {cache_dir}")
    logger.info(f"Playbook: {playbook}")

    return {'return': 0}


def postprocess(i):
    env = i['env']
    logger = i['automation'].logger

    logger.info("Ansible playbook execution completed")

    return {'return': 0}
