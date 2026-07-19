"""mlc-scripts — MLPerf automation script content bundled as pip package data.

This package ships the ~378 automation script directories (``meta.yaml`` +
``customize.py`` + ``run.sh``) that the mlcflow engine executes. As of the
Option B migration these are delivered via ``pip install mlc-scripts`` instead
of a runtime ``git clone`` of mlperf-automations.

Public attributes
-----------------
SCRIPTS_DIR : str
    Absolute path to the bundled ``script/`` directory (read-only package data).
CACHE_DIR : str
    Where script execution artifacts + cached state are written. Defaults to
    ``{package}/cache`` (per-venv isolation). Override with the ``MLC_CACHE_DIR``
    environment variable — e.g. point it at ``~/MLC/repos/local/cache`` to reuse
    a pre-migration cache without moving data, or at a large-disk mount for
    multi-TB dataset caches.
"""

import os

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "script")

CACHE_DIR = os.environ.get(
    "MLC_CACHE_DIR",
    os.path.join(os.path.dirname(__file__), "cache"),
)

# Created lazily at first use rather than shipped in the wheel. When
# MLC_CACHE_DIR points at a pre-existing location this simply ensures it exists.
os.makedirs(CACHE_DIR, exist_ok=True)

__all__ = ["SCRIPTS_DIR", "CACHE_DIR"]
