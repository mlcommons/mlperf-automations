#!/bin/bash

CUR=$PWD

if [[ ${MLC_CRITEO_FAKE} == "yes" ]]; then
  exit 0
fi
#${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/preprocess.py
