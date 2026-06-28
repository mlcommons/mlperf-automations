from mlc import utils
import os
import subprocess
import stat


def preprocess(i):

    env = i['env']
    state = i['state']

    env_key = env.get('MLC_PASS_ENV_KEY', '')
    secret_name = env.get('MLC_PASS_SECRET_NAME', '')
    source = env.get('MLC_PASS_SOURCE', 'file')

    if not env_key:
        return {'return': 1, 'error': 'MLC_PASS_ENV_KEY is not set. Please provide --env_key (e.g., MLC_UPLOAD_API_TOKEN)'}

    if not secret_name:
        return {'return': 1, 'error': 'MLC_PASS_SECRET_NAME is not set. Please provide --secret_name'}

    secret_value = ''

    if source == 'file':
        secret_value = _read_from_file(env, secret_name)
    elif source == 'env':
        secret_value = os.environ.get(secret_name, '')
    elif source == 'pass':
        secret_value = _read_from_pass(secret_name)
    elif source == 'keyring':
        secret_value = _read_from_keyring(secret_name)
    else:
        return {'return': 1, 'error': f'Unknown source: {source}. Use file, env, pass, or keyring.'}

    if not secret_value:
        return {'return': 1, 'error': f'Secret "{secret_name}" not found via source "{source}"'}

    env[env_key] = secret_value

    # No command to run - secret is loaded into env
    env['MLC_RUN_CMD'] = 'echo "Secret loaded successfully into ${MLC_PASS_ENV_KEY}"'

    return {'return': 0}


def _read_from_file(env, secret_name):
    """Read a secret from a credentials file (KEY=VALUE format)."""
    creds_file = os.path.expanduser(env.get('MLC_PASS_CREDENTIALS_FILE', '~/.mlc_credentials'))

    if not os.path.exists(creds_file):
        return ''

    # Check file permissions (warn if too open)
    file_stat = os.stat(creds_file)
    file_mode = stat.S_IMODE(file_stat.st_mode)
    if file_mode & (stat.S_IRGRP | stat.S_IROTH):
        print(f'WARNING: {creds_file} has group/other read permissions. Run: chmod 600 {creds_file}')

    with open(creds_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key == secret_name:
                    return value
    return ''


def _read_from_pass(secret_name):
    """Read a secret from the 'pass' password store."""
    try:
        result = subprocess.run(
            ['pass', 'show', secret_name],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ''


def _read_from_keyring(secret_name):
    """Read a secret from the system keyring."""
    try:
        import keyring
        # secret_name format: "service/username" or just "service"
        parts = secret_name.split('/', 1)
        service = parts[0]
        username = parts[1] if len(parts) > 1 else 'default'
        return keyring.get_password(service, username) or ''
    except ImportError:
        return ''


def postprocess(i):

    env = i['env']
    state = i['state']

    return {'return': 0}
