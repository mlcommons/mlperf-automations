#!/bin/bash

cmd="${MLC_CONDA_BIN_WITH_PATH} create -p ${PWD}"
echo "$cmd"
eval "$cmd"
test $? -eq 0 || exit $?

