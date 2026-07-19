#!/bin/bash

${MLC_PYTHON_BIN_WITH_PATH} -m pip install --upgrade pip
test $? -eq 0 || exit $?
