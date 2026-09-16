"""
mlc_compat: script-level mlcflow version-compatibility helpers.

Scripts declare version requirements via mlc_compat in their meta.yaml.
This module evaluates those requirements and formats user-facing notices.
Version comparison delegates to mlc.utils.compare_versions (already
available in every mlcflow environment) so no new dependency is needed.
"""
import os
import mlc.utils as utils


def get_installed_version():
    """Return the installed mlcflow version string, or None if unavailable."""
    try:
        from importlib.metadata import version
        return version("mlcflow")
    except Exception:
        pass
    # Fallback: read the VERSION file bundled with the mlcflow package
    try:
        import mlc
        version_file = os.path.join(
            os.path.dirname(
                mlc.__file__), "..", "VERSION")
        with open(version_file) as f:
            return f.read().strip()
    except Exception:
        return None


def check_mlc_compat(compat_entries, installed_version_str):
    """
    Evaluate mlc_compat entries against installed_version_str.

    Args:
        compat_entries (list[dict]): mlc_compat list from a script's meta.yaml.
        installed_version_str (str | None): Installed mlcflow version.

    Returns:
        (unmet_warnings, unmet_blockers): Two lists of dicts with keys
        'min_version' and 'message'.  Blockers have fail: true in the source.
    """
    if not compat_entries or not installed_version_str:
        return [], []

    unmet_warnings = []
    unmet_blockers = []
    for entry in compat_entries:
        if not isinstance(entry, dict):
            continue
        min_version_str = entry.get("min_version", "")
        message = entry.get("message", "")
        fail = bool(entry.get("fail", False))
        if not min_version_str:
            continue
        try:
            if utils.compare_versions(
                    installed_version_str, min_version_str) < 0:
                item = {"min_version": min_version_str, "message": message}
                if fail:
                    unmet_blockers.append(item)
                else:
                    unmet_warnings.append(item)
        except Exception:
            continue

    return unmet_warnings, unmet_blockers


def format_compat_notice(script_name, unmet_warnings,
                         unmet_blockers, installed_version_str):
    """
    Build a consolidated human-readable notice for unmet mlc_compat requirements.

    Returns:
        (notice_str, is_blocking): notice_str is empty when all requirements
        are satisfied.  is_blocking is True when any blocker is unmet.
    """
    all_unmet = unmet_warnings + unmet_blockers
    if not all_unmet:
        return "", False

    is_blocking = bool(unmet_blockers)
    lines = [
        "mlc_compat: script '{}' has version requirements not met by "
        "the installed mlcflow {}:".format(
            script_name, installed_version_str or "(unknown)")
    ]
    for entry in unmet_warnings:
        lines.append(
            "  [warn ] min_version {}: {}".format(
                entry["min_version"],
                entry["message"]))
    for entry in unmet_blockers:
        lines.append(
            "  [ERROR] min_version {}: {}".format(
                entry["min_version"],
                entry["message"]))
    if is_blocking:
        lines.append(
            "  -> Run `pip install --upgrade mlcflow` to satisfy blocking requirements.")
    else:
        lines.append(
            "  -> Consider upgrading: `pip install --upgrade mlcflow`")

    return "\n".join(lines), is_blocking
