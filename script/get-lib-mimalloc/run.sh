#!/bin/bash

set -e

#Add your run commands here...
# run "$MLC_RUN_CMD"
cd ${MLC_MIMALLOC_SRC_PATH}
mkdir -p obj
cd obj
echo "${MLC_MIMALLOC_CMAKE_COMMAND}"
${MLC_MIMALLOC_CMAKE_COMMAND}
make
