#!/bin/bash

${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/code.py
test $? -eq 0 || exit 1
