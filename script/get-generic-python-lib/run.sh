#!/bin/bash

MLC_TMP_CURRENT_SCRIPT_PATH="${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}"

"${MLC_PYTHON_BIN_WITH_PATH}" "${MLC_TMP_CURRENT_SCRIPT_PATH}/detect-version.py"
test $? -eq 0 || exit $?
exit 0
