#!/bin/bash
function cmake() {
${MLC_CMAKE_BIN_WITH_PATH} $@
}

export CC=${MLC_C_COMPILER_WITH_PATH}
export CXX=${MLC_CXX_COMPILER_WITH_PATH}

CUR=$PWD
mkdir -p install
INSTALL_DIR=$CUR/install
cd ${MLC_GIT_REPO_CHECKOUT_PATH}

mkdir build
cd build
export MAKEFLAGS=-j${MLC_MAKE_CORES}
cmake -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR} ..
test $? -eq 0 || exit $?

CMD="make install"
echo ${CMD}
eval $CMD
test $? -eq 0 || exit $?
