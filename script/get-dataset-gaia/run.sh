#!/bin/bash
# Fetch GAIA (gated HF dataset) into a cached jsonl. customize.py skips the
# command when a local --data_path was given.
if [[ -n "${MLC_RUN_CMD:-}" ]]; then
  echo "${MLC_RUN_CMD}"
  eval "${MLC_RUN_CMD}"
  test $? -eq 0 || exit $?
fi
