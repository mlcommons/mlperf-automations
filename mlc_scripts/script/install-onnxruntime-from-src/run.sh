#!/bin/bash

export CC=${MLC_GCC_BIN_WITH_PATH}
export CXX=${MLC_GCC_INSTALLED_PATH}/g++

echo "cd ${MLC_RUN_DIR}"
cd ${MLC_RUN_DIR}
test $? -eq 0 || exit $?
rm -rf build

echo ${MLC_RUN_CMD}
eval ${MLC_RUN_CMD}
test $? -eq 0 || exit $?

exit 1
