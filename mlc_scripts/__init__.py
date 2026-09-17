"""Packaged MLC script content.

The repo root's ``meta.yaml`` and ``script/`` tree are copied in here at build
time (see ``BuildPyWithScriptContent`` in setup.py), so an installed
``mlc-scripts`` *is* the scripts rather than instructions for fetching them.

mlcflow locates this directory through ``importlib.metadata`` and registers it
as an ordinary non-git repo.
"""
