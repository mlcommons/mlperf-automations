"""Resolve a registered repo's code version (git commit / branch / dirty state).

Script outputs (e.g. the MLPerf system-info JSONs) need to record the exact code
that produced them. mlc-scripts has no tagged release — users track it with a
plain ``git pull`` — so the Git commit of the automations checkout is the version.

A repo's version changes only when the repo changes (pull / checkout / commit /
local edit), never between two back-to-back ``mlc`` commands. Running ``git`` on
every invocation would add a subprocess spawn per repo for a value that rarely
moves. So we cache the result in a sidecar (``repos_version.json``) keyed by repo
path and recompute only when ``.git/HEAD`` or ``.git/index`` mtime changes — the
same mtime-gating trick ``index.py`` uses for ``modified_times.json``.

Caveat: ``commit`` and ``branch`` are always accurate (HEAD/index move on every
pull / checkout / commit). The ``dirty`` flag is best-effort — editing a tracked
file without staging it does not touch ``.git/index``, so a freshly-dirtied tree
can report ``dirty: false`` until the next git operation. ``commit`` remains the
authoritative version identifier.

Resolution order (so the result is never empty):
  1. git         — rev-parse HEAD + branch + dirty flag
  2. commit_file — git_commit_hash.txt written at build time (pip installs)
  3. package     — installed mlc-scripts package version
  4. unknown     — nothing could be resolved
"""

import os
import re
import json
import logging
import subprocess

try:
    import filelock
except Exception:  # pragma: no cover - filelock is a declared dependency
    filelock = None

logger = logging.getLogger(__name__)

SIDECAR_NAME = "repos_version.json"

# Seconds to wait for the sidecar lock before falling back to an uncached
# compute. Kept as a module constant so it is easy to tune in one place.
_LOCK_TIMEOUT = 10

# Seconds to allow a single git subprocess before giving up (guards against a
# hung git so version resolution can never block a script run indefinitely).
_GIT_TIMEOUT = 30

# Keys stored only for cache invalidation; stripped from the returned version.
_CACHE_ONLY_KEYS = ("head_mtime", "index_mtime")

# A git commit is an abbreviated-to-full hex SHA (sha1 is 40, sha256 is 64).
_COMMIT_RE = re.compile(r"\A[0-9a-fA-F]{7,64}\Z")


def _looks_like_commit(value):
    return bool(value) and bool(_COMMIT_RE.match(value))


def _git(repo_path, *args):
    return subprocess.check_output(
        ["git", "-C", repo_path, *args],
        stderr=subprocess.DEVNULL, text=True, timeout=_GIT_TIMEOUT).strip()


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def _compute_from_git(repo_path):
    commit = _git(repo_path, "rev-parse", "HEAD")
    branch = _git(repo_path, "rev-parse", "--abbrev-ref", "HEAD")
    # -uno: ignore untracked files; we only care about tracked-file changes.
    dirty = bool(_git(repo_path, "status", "--porcelain", "-uno"))
    return {"source": "git", "commit": commit,
            "branch": branch, "dirty": dirty}


def _fallback(repo_path):
    """Resolve a version without git: build hash file, then package version."""
    hash_file = os.path.join(repo_path, "git_commit_hash.txt")
    if os.path.isfile(hash_file):
        try:
            with open(hash_file) as f:
                commit = f.read().strip()
            if _looks_like_commit(commit):
                return {"source": "commit_file", "commit": commit,
                        "branch": "", "dirty": False}
            if commit:
                logger.debug(
                    "git_commit_hash.txt in %s is not a valid commit hash: %r",
                    repo_path, commit)
            else:
                logger.debug("git_commit_hash.txt in %s is empty", repo_path)
        except OSError as e:
            logger.debug("Could not read %s: %s", hash_file, e)
    else:
        logger.debug("No git_commit_hash.txt in %s", repo_path)
    try:
        from importlib.metadata import version, PackageNotFoundError
        try:
            return {"source": "package", "commit": "", "branch": "",
                    "dirty": False, "version": version("mlc-scripts")}
        except PackageNotFoundError:
            logger.debug("mlc-scripts package metadata not found")
    except Exception as e:
        logger.debug("mlc-scripts version lookup failed: %s", e)
    logger.debug(
        "Could not resolve a version for %s (source=unknown)", repo_path)
    return {"source": "unknown", "commit": "", "branch": "", "dirty": False}


def _strip_cache_keys(entry):
    return {k: v for k, v in entry.items() if k not in _CACHE_ONLY_KEYS}


def get_repo_version(repo_path, repos_path):
    """Return a version dict for ``repo_path`` using an mtime-gated sidecar cache.

    Args:
      repo_path:  absolute path to the repo checkout.
      repos_path: the MLC repos root (where the sidecar cache lives).

    Returns a dict with at least ``source`` and (when available) ``commit``,
    ``branch``, ``dirty`` and ``version``.

    Notes:
      ``commit`` / ``branch`` are authoritative. ``dirty`` is best-effort: it
      uses ``git status --porcelain -uno`` (untracked files are intentionally
      ignored), and because the result is cached behind ``.git/HEAD`` /
      ``.git/index`` mtimes, an unstaged edit to a tracked file may not refresh
      it until the next git operation. Treat ``dirty`` as a hint, not a
      guarantee.
    """
    # Normalise so the sidecar cache key is stable regardless of how the caller
    # spelled the path (relative vs absolute, symlinks, trailing slash).
    repo_path = os.path.realpath(repo_path)
    git_dir = os.path.join(repo_path, ".git")
    head_mtime = _mtime(os.path.join(git_dir, "HEAD"))

    if head_mtime is None:
        # No .git/HEAD to mtime-gate on. If .git still exists (e.g. a git
        # worktree/submodule where .git is a FILE, not a directory), git
        # commands still work via `git -C` but we have no cheap change signal,
        # so compute fresh and uncached. If .git is absent entirely (e.g. a pip
        # install), fall back to the hash file / package version.
        if os.path.exists(git_dir):
            try:
                return _compute_from_git(repo_path)
            except Exception as e:
                logger.debug(
                    "git version failed for %s: %s; falling back",
                    repo_path, e)
                return _fallback(repo_path)
        return _fallback(repo_path)

    index_mtime = _mtime(os.path.join(git_dir, "index"))

    def _resolve():
        try:
            return _compute_from_git(repo_path)
        except Exception as e:
            logger.debug(
                "git version failed for %s: %s; falling back", repo_path, e)
            return _fallback(repo_path)

    sidecar = os.path.join(repos_path, SIDECAR_NAME)

    # Without filelock we still work correctly, just uncached.
    if filelock is None:
        logger.debug(
            "filelock unavailable; computing repo version uncached")
        return _resolve()

    lock = filelock.FileLock(sidecar + ".lock")
    try:
        with lock.acquire(timeout=_LOCK_TIMEOUT):
            cache = {}
            if os.path.isfile(sidecar):
                try:
                    with open(sidecar) as f:
                        cache = json.load(f)
                    if not isinstance(cache, dict):
                        cache = {}
                except (json.JSONDecodeError, OSError) as e:
                    logger.debug(
                        "Ignoring unreadable %s (%s); rebuilding", sidecar, e)
                    cache = {}

            entry = cache.get(repo_path)
            if (isinstance(entry, dict)
                    and entry.get("head_mtime") == head_mtime
                    and entry.get("index_mtime") == index_mtime):
                # Cheap path: nothing changed since we last computed.
                return _strip_cache_keys(entry)

            info = _resolve()
            cache[repo_path] = {**info, "head_mtime": head_mtime,
                                "index_mtime": index_mtime}
            try:
                with open(sidecar, "w") as f:
                    json.dump(cache, f, indent=2)
            except OSError:
                pass
            return info
    except Exception as e:
        # Lock timeout or any I/O problem: compute without caching.
        logger.debug(
            "repos_version cache unavailable (%s); computing uncached", e,
            exc_info=True)
        return _resolve()
