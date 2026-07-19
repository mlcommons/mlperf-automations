#!/bin/bash

CUR_DIR=$PWD
rm -rf onednn
cp -r ${MLC_ONEDNN_SRC_REPO_PATH} onednn
cd onednn
test "${?}" -eq "0" || exit $?
rm -rf build

mkdir build
cd build
cmake ..
test "${?}" -eq "0" || exit $?
make  -j${MLC_HOST_CPU_PHYSICAL_CORES_PER_SOCKET}
test "${?}" -eq "0" || exit $?
