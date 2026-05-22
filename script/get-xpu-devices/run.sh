#!/bin/bash

pushd "${MLC_TMP_CURRENT_PATH}"
MLC_PYTHON_BIN_WITH_PATH=${MLC_PYTHON_BIN_WITH_PATH:-python3}

"${MLC_PYTHON_BIN_WITH_PATH}" "${MLC_TMP_CURRENT_SCRIPT_PATH}/detect.py"
test $? -eq 0 || exit $?

popd