#!/bin/bash

CUR=$PWD
echo ${MLC_RUN_CMD}
eval ${MLC_RUN_CMD}
test $? -eq 0 || exit $?
