#!/bin/bash

${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/src/main.py ${MLC_RUN_OPTS}
test $? -eq 0 || exit 1
