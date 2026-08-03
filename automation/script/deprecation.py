# One-time notice for users still running the engine copy kept in this repo.
#
# mlcflow >= 1.3.0 bundles its own copy of automation/ and never loads this
# one, so reaching this code means the installed mlcflow predates the
# migration of the engine into mlcflow.

import os

from utils import compare_versions

MIN_MLCFLOW_VERSION = "1.3.0"

_ENV_SENTINEL = "MLC_ENGINE_DEPRECATION_NOTICE_SHOWN"

_notice_shown = False


def get_mlcflow_version():
    """
    Best-effort lookup of the installed mlcflow version.

    Returns the version string, or None if it cannot be determined.
    """

    # The distribution is named "mlcflow" - note that looking up "mlc"
    # always raises PackageNotFoundError.
    try:
        from importlib.metadata import version
        return version("mlcflow")
    except Exception:
        pass

    try:
        import mlc
        return mlc.__version__
    except Exception:
        return None


def notify_if_deprecated(logger):
    """
    Warn once per process that this copy of the engine is deprecated.

    Stays silent when the installed mlcflow is recent enough, or when its
    version cannot be determined. Never raises.
    """

    global _notice_shown

    if _notice_shown or os.environ.get(_ENV_SENTINEL):
        return

    try:
        current_version = get_mlcflow_version()
        if not current_version:
            return

        r = compare_versions({'version1': current_version,
                              'version2': MIN_MLCFLOW_VERSION})
        if r.get('return', 0) > 0 or r.get('comparison', 0) >= 0:
            return

        _notice_shown = True
        os.environ[_ENV_SENTINEL] = 'yes'

        logger.warning(
            'Your mlcflow version ({}) is deprecated and will stop being supported soon.\n'
            '  The MLC script automation engine has moved into mlcflow itself and now ships with it.\n'
            '  This run is using the older fallback copy kept in mlcommons@mlperf-automations,\n'
            '  which will be removed once the migration is complete.\n'
            '  Please upgrade to mlcflow >= {}:  pip install --upgrade mlcflow'.format(
                current_version, MIN_MLCFLOW_VERSION))

    except Exception:
        # Showing a notice must never be able to break a run.
        pass
