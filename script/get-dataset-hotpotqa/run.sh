#!/bin/bash
# Convert the downloaded HotpotQA split into the harness JSON schema (cached).
# When a local --data_path was given, customize.py skips the conversion command.
if [[ -n "${MLC_RUN_CMD:-}" ]]; then
  echo "${MLC_RUN_CMD}"
  eval "${MLC_RUN_CMD}"
  test $? -eq 0 || exit $?
fi
