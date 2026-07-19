#!/bin/bash

MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}
${MLC_CXX_COMPILER_WITH_PATH} -O3 ${MLC_TMP_CURRENT_SCRIPT_PATH}/src/classification.cpp -o classification.exe -ltensorflow

test $? -eq 0 || exit 1
