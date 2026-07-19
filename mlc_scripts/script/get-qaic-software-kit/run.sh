#!/bin/bash

function cmake() {
${MLC_CMAKE_BIN_WITH_PATH} $@
}

export CC=${MLC_C_COMPILER_WITH_PATH}
export CXX=${MLC_CXX_COMPILER_WITH_PATH}

export -f cmake
cd ${MLC_QAIC_SOFTWARE_KIT_PATH}
rm -rf build
./bootstrap.sh
test $? -eq 0 || exit $?
cd build
../scripts/build.sh -b Release
test $? -eq 0 || exit $?
