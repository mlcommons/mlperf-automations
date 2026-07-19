#!/bin/bash

CUR_DIR=$PWD
rm -rf gflags
cp -r ${MLC_GFLAGS_SRC_REPO_PATH} gflags
cd gflags
test "${?}" -eq "0" || exit $?
rm -rf build

mkdir build
cd build
cmake ..
test "${?}" -eq "0" || exit $?
make  -j${MLC_HOST_CPU_PHYSICAL_CORES_PER_SOCKET}
test "${?}" -eq "0" || exit $?
