#!/bin/bash

cmd="${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/process.py"

echo $cmd

eval $cmd
