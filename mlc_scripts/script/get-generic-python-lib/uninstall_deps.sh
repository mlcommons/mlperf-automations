#!/bin/bash

if [[ -n ${MLC_GENERIC_PYTHON_PIP_UNINSTALL_DEPS} ]]; then
    cmd="${MLC_PYTHON_BIN_WITH_PATH} -m pip uninstall ${MLC_GENERIC_PYTHON_PIP_UNINSTALL_DEPS} -y ${MLC_PYTHON_PIP_COMMON_EXTRA}"
    echo "$cmd"
    eval "$cmd"
    test $? -eq 0 || exit $?
fi
