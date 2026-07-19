#!/bin/bash

${MLC_PYTHON_BIN} ${MLC_TMP_CURRENT_SCRIPT_PATH}/process.py
test $? -eq 0 || exit 1
