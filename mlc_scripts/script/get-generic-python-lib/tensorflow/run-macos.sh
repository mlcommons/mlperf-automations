#!/bin/bash

MLC_PYTHON_BIN=${MLC_PYTHON_BIN:-python3}

${MLC_PYTHON_BIN} -m pip install tensorflow-macos${MLC_TMP_PIP_VERSION_STRING}
test $? -eq 0 || exit 1
echo "MLC_GENERIC_PYTHON_PACKAGE_NAME=tensorflow-macos" >> $PWD/tmp-run-env.out
