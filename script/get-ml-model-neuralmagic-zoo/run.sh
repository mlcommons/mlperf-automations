#!/bin/bash
cmd="${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/download_sparse.py"
echo "$cmd"
eval "$cmd"
test $? -eq 0 || exit $?
