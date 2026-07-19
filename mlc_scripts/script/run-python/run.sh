#!/bin/bash

${MLC_PYTHON_BIN_WITH_PATH} ${MLC_RUN_PYTHON_CMD}
test $? -eq 0 || exit $?
