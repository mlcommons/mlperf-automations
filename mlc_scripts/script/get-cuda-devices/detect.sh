#!/bin/bash

${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/detect.py
test $? -eq 0 || exit 11
