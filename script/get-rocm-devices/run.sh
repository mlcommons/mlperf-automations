#!/bin/bash

cd ${MLC_TMP_CURRENT_PATH}

${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/detect.py > tmp-run.out
test $? -eq 0 || exit $?
cat tmp-run.out
test $? -eq 0 || exit $?
