#!/bin/bash

MLC_TMP_CURRENT_SCRIPT_PATH="${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}"
cmd="${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/detect-version.py"
echo $cmd
eval $cmd
test $? -eq 0 || exit $?
exit 0
