"""Resolve a registered repo's code version (git commit / branch / dirty state).

Script outputs (e.g. the MLPerf system-info JSONs) need to record the exact code
that produced them. mlc-scripts has no tagged release — users track it with a
plain ``git pull`` — so the Git commit of the automations checkout is the version.

A repo's version changes only when the repo changes (pull / checkout / commit /
local edit), never between two back-to-back ``mlc`` commands. Running ``git`` on
every invocation would add a subprocess spawn per repo for a value that rarely
moves. So we cache the result in a sidecar (``repos_version.json``) keyed by repo
path and recompute only when ``.git/HEAD`` or ``.git/index`` mtime changes.

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
import json
import subprocess

try:
    import filelock
except Exception:  # filelock is an mlcflow dependency; degrade gracefully
    filelock = None

SIDECAR_NAME = "repos_version.json"

# Keys stored only for cache invalidation; stripped from the returned version.
_CACHE_ONLY_KEYS = ("head_mtime", "index_mtime")


def _git(repo_path, *args):
    return subprocess.check_output(
        ["git", "-C", repo_path, *args],
        stderr=subprocess.DEVNULL, text=True).strip()


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
            if commit:
                return {"source": "commit_file", "commit": commit,
                        "branch": "", "dirty": False}
        except OSError:
            pass
    try:
        from importlib.metadata import version, PackageNotFoundError
        try:
            return {"source": "package", "commit": "", "branch": "",
                    "dirty": False, "version": version("mlc-scripts")}
        except PackageNotFoundError:
            pass
    except Exception:
        pass
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
    """
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
            except Exception:
                return _fallback(repo_path)
        return _fallback(repo_path)

    index_mtime = _mtime(os.path.join(git_dir, "index"))

    def _resolve():
        try:
            return _compute_from_git(repo_path)
        except Exception:
            return _fallback(repo_path)

    sidecar = os.path.join(repos_path, SIDECAR_NAME)

    # Without filelock we still work correctly, just uncached.
    if filelock is None:
        return _resolve()

    lock = filelock.FileLock(sidecar + ".lock")
    try:
        with lock.acquire(timeout=10):
            cache = {}
            if os.path.isfile(sidecar):
                try:
                    with open(sidecar) as f:
                        cache = json.load(f)
                    if not isinstance(cache, dict):
                        cache = {}
                except (json.JSONDecodeError, OSError):
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
    except Exception:
        # Lock timeout or any I/O problem: compute without caching.
        return _resolve()
