from mlc import utils
from utils import is_true
import os
import subprocess


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    automation = i['automation']
    logger = automation.logger

    if os_info['platform'] == 'windows':
        return {'return': 1, 'error': 'isolate-run is not supported on Windows'}

    sudo = env.get('MLC_SUDO', 'sudo')
    undo = not is_true(env.get('MLC_ISOLATE_NO_UNDO', ''))
    cmds = []

    # --- User isolation: prevent new logins ---
    if is_true(env.get('MLC_ISOLATE_NO_NEW_LOGINS', '')):
        if undo:
            cmds.append(f'{sudo} rm -f /var/run/nologin')
            logger.info('Undo: removing /var/run/nologin to allow new logins')
        else:
            cmds.append(f'{sudo} touch /var/run/nologin')
            logger.info('Blocking new user logins via /var/run/nologin')

    # --- User isolation: force logout other users ---
    if is_true(env.get('MLC_ISOLATE_FORCE_LOGOUT', '')):
        if undo:
            logger.info('Undo: no action needed for force-logout (already done)')
        else:
            logger.info('Forcing logout of all other user sessions')

    # --- Network isolation: disconnect network ---
    if is_true(env.get('MLC_ISOLATE_NETWORK', '')):
        if undo:
            logger.info('Undo: re-enabling network interfaces')
        else:
            logger.info('Disconnecting non-loopback network interfaces')

    env['MLC_ISOLATE_CMDS'] = ' && '.join(cmds) if cmds else ''

    return {'return': 0}


def _get_current_user():
    """Get the current username."""
    return os.environ.get('USER') or os.environ.get('USERNAME') or 'unknown'


def _get_other_user_sessions(logger):
    """Get list of other logged-in user sessions (tty/pts)."""
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
                iface = parts[1].strip()
                if iface != 'lo':
                    interfaces.append(iface)
    except Exception as e:
        logger.warning(f'Failed to list network interfaces: {e}')
    return interfaces


def postprocess(i):

    env = i['env']

    return {'return': 0}
