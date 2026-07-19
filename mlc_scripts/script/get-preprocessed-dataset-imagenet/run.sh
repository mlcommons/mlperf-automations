#!/bin/bash
if [ ! -z "${MLC_IMAGENET_PREPROCESSED_PATH+x}" ]; then
    exit 0
fi
"${MLC_PYTHON_BIN_WITH_PATH}" "${MLC_TMP_CURRENT_SCRIPT_PATH}/preprocess.py"
test $? -eq 0 || exit 1
