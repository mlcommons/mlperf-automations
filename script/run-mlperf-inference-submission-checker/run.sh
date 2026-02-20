#!/bin/bash
cmd=${MLC_RUN_CMD}
echo "${cmd}"
eval "${cmd}"
MLC_RUN_STATUS=$? # capture the exit code

cmd=${MLC_POST_RUN_CMD}
echo "${cmd}"
eval "${cmd}"
test $? -eq 0 || exit $?

${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/code.py
test $? -eq 0 || exit $?

test ${MLC_RUN_STATUS} -eq 0 || exit ${MLC_RUN_STATUS}