#!/bin/bash


cmd="${MLC_CONDA_PKG_INSTALL_CMD}"
echo $cmd
eval $cmd
test $? -eq 0 || exit $?
