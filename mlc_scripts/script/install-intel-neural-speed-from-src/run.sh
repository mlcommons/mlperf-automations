#!/bin/bash

CUR_DIR=$PWD
echo $PWD
rm -rf neural-speed
cmd="cp -r ${MLC_INTEL_NEURAL_SPEED_SRC_REPO_PATH} neural-speed"
echo "$cmd"
eval "$cmd"
${MLC_PYTHON_BIN_WITH_PATH} -m pip install -r neural-speed/requirements.txt
test $? -eq 0 || exit $?
CMAKE_ARGS="-DNS_PROFILING=ON" ${MLC_PYTHON_BIN_WITH_PATH} -m pip install -ve ./neural-speed
test $? -eq 0 || exit $?

echo "******************************************************"
