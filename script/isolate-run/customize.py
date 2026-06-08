from mlc import utils
from utils import is_true
import os
import json
import subprocess


STATE_FILE = 'isolate_state.json'


def _get_state_path(env):
    """Get path to state file."""
    state_dir = env.get('MLC_ISOLATE_STATE_DIR', '/tmp/mlc-isolate-state')
    return os.path.join(state_dir, STATE_FILE)


def _save_state(state, env, logger):
    """Save isolation state to file."""
    state_dir = env.get('MLC_ISOLATE_STATE_DIR', '/tmp/mlc-isolate-state')
    os.makedirs(state_dir, exist_ok=True)
    path = os.path.join(state_dir, STATE_FILE)
    with open(path, 'w') as f:
        json.dump(state, f, indent=2)
    logger.info(f'Saved isolation state to {path}')


def _load_state(env, logger):
    """Load saved isolation state."""
    path = _get_state_path(env)
    if not os.path.exists(path):
        logger.warning(f'No saved state found at {path}')
        return {}
    with open(path, 'r') as f:
        state = json.load(f)
    logger.info(f'Loaded isolation state from {path}')
    return state


def _get_current_user():
    """Get the current username."""
    return os.environ.get('USER') or os.environ.get('USERNAME') or 'unknown'


def _get_other_user_sessions(logger):
    """Get list of other logged-in user sessions."""
    current_user = _get_current_user()
    sessions = []
    try:
        result = subprocess.run(
            ['who'], capture_output=True, text=True)
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                user, tty = parts[0], parts[1]
                if user != current_user:
                    sessions.append((user, tty))
    except Exception as e:
        logger.warning(f'Failed to get user sessions: {e}')
    return sessions


def _get_active_interfaces(logger):
    """Get list of active non-loopback network interfaces."""
    interfaces = []
    try:
        result = subprocess.run(
            ['ip', '-o', 'link', 'show', 'up'],
            capture_output=True, text=True)
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split(':')
            if len(parts) >= 2:
                iface = parts[1].strip().split('@')[0]
                if iface != 'lo':
                    interfaces.append(iface)
    except Exception as e:
        logger.warning(f'Failed to list network interfaces: {e}')
    return interfaces


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    automation = i['automation']
    logger = automation.logger

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'isolate-run is not supported on Windows'}

    action = env.get('MLC_ISOLATE_ACTION', '')
    if action not in ('set', 'unset'):
        return {'return': 1, 'error': 'Must specify action variation: _set or _unset'}

    if action == 'set':
        # Save current state before applying isolation
        state = {}

        if is_true(env.get('MLC_ISOLATE_NO_NEW_LOGINS', '')):
            state['nologin_existed'] = os.path.exists('/var/run/nologin')
            logger.info(f'State: /var/run/nologin existed = {state["nologin_existed"]}')
            logger.info('Will block new user logins via /var/run/nologin')

        if is_true(env.get('MLC_ISOLATE_FORCE_LOGOUT', '')):
            sessions = _get_other_user_sessions(logger)
            state['other_users'] = [s[0] for s in sessions]
            logger.info(f'State: other logged-in users = {state["other_users"]}')
            logger.info('Will force logout all other user sessions')

        if is_true(env.get('MLC_ISOLATE_NETWORK', '')):
            interfaces = _get_active_interfaces(logger)
            state['active_interfaces'] = interfaces
            logger.info(f'State: active interfaces = {interfaces}')
            logger.info('Will disable non-loopback network interfaces')
            # Pass saved interfaces to run.sh so it knows exactly which to bring down
            env['MLC_ISOLATE_SAVED_INTERFACES'] = ','.join(interfaces)

        _save_state(state, env, logger)

    elif action == 'unset':
        # Load saved state to know what to restore
        state = _load_state(env, logger)

        if is_true(env.get('MLC_ISOLATE_NO_NEW_LOGINS', '')):
            nologin_existed = state.get('nologin_existed', False)
            env['MLC_ISOLATE_NOLOGIN_EXISTED'] = 'yes' if nologin_existed else 'no'
            if nologin_existed:
                logger.info('State shows /var/run/nologin existed before set - will leave it')
            else:
                logger.info('State shows /var/run/nologin did not exist before set - will remove it')

        if is_true(env.get('MLC_ISOLATE_FORCE_LOGOUT', '')):
            logger.info('Unset: no action for force-logout (cannot restore terminated sessions)')

        if is_true(env.get('MLC_ISOLATE_NETWORK', '')):
            interfaces = state.get('active_interfaces', [])
            env['MLC_ISOLATE_SAVED_INTERFACES'] = ','.join(interfaces)
            logger.info(f'Will re-enable interfaces: {interfaces}')

    return {'return': 0}


def postprocess(i):

    env = i['env']

    return {'return': 0}
