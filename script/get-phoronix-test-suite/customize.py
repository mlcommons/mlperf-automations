from mlc import utils
import os
import shutil

from utils import is_true


def _resolve_launcher(path):
    """Return the phoronix-test-suite launcher given a dir or the launcher path."""
    if not path:
        return ''
    if os.path.isfile(path) and os.access(path, os.X_OK):
        return path
    if os.path.isdir(path):
        for cand in (os.path.join(path, 'bin', 'phoronix-test-suite'),
                     os.path.join(path, 'phoronix-test-suite')):
            if os.path.isfile(cand):
                return cand
    return ''


def preprocess(i):

    env = i['env']
    logger = i['automation'].logger

    user_path = env.get('MLC_PHORONIX_TEST_SUITE_PATH', '')
    prefix = env.get('MLC_PHORONIX_INSTALL_PREFIX', '')
    bin_path = ''

    if user_path:
        bin_path = _resolve_launcher(user_path)
        if not bin_path:
            return {'return': 1,
                    'error': f"phoronix-test-suite not found at MLC_PHORONIX_TEST_SUITE_PATH={user_path}"}
    else:
        # Reuse an install already on PATH before downloading anything.
        which = shutil.which('phoronix-test-suite')
        if which:
            bin_path = which
        elif prefix:
            # Reuse a prior no-sudo install in this prefix if present.
            bin_path = _resolve_launcher(prefix)
            if not bin_path:
                # run.sh will perform the no-sudo portable install into the
                # prefix.
                env['MLC_PHORONIX_DO_PORTABLE_INSTALL'] = 'yes'

    if bin_path:
        env['MLC_PHORONIX_TEST_SUITE_BIN_WITH_PATH'] = bin_path
        env['MLC_PHORONIX_SKIP_INSTALL'] = 'yes'
        logger.info(f"Using existing phoronix-test-suite: {bin_path}")
    elif not prefix:
        # No reusable install and no prefix: fall back to the system .deb/apt path.
        # Guard against the no-sudo case where apt will fail.
        no_sudo = is_true(env.get('MLC_PHORONIX_NO_SUDO', '')) or \
            (env.get('MLC_SUDO_USER', '') not in ('yes', 'True', 'true', True))
        if no_sudo:
            return {'return': 1,
                    'error': 'phoronix-test-suite is not installed and sudo is unavailable. '
                             'Pass --install_prefix=<shared dir> for a no-sudo install, '
                             'or --phoronix_path=<existing install>.'}

    return {'return': 0}


def postprocess(i):

    env = i['env']
    logger = i['automation'].logger

    bin_path = env.get('MLC_PHORONIX_TEST_SUITE_BIN_WITH_PATH', '')
    prefix = env.get('MLC_PHORONIX_INSTALL_PREFIX', '')

    if not bin_path and prefix:
        bin_path = _resolve_launcher(prefix)
    if not bin_path:
        bin_path = shutil.which('phoronix-test-suite') or ''
        if not bin_path and os.path.isfile('/usr/bin/phoronix-test-suite'):
            bin_path = '/usr/bin/phoronix-test-suite'

    if not bin_path:
        return {'return': 1,
                'error': 'phoronix-test-suite not found after installation'}

    env['MLC_PHORONIX_TEST_SUITE_BIN_WITH_PATH'] = bin_path
    env['MLC_PHORONIX_INSTALLED_PATH'] = os.path.dirname(bin_path)
    logger.info(f"phoronix-test-suite: {bin_path}")
    return {'return': 0}
