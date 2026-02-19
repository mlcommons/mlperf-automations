#!/bin/bash

set -e

#Add your run commands here...
# run "$MLC_RUN_CMD"

mkdir -p lib
cd lib
echo "${MLC_MIMALLOC_CMAKE_COMMAND}"
${MLC_MIMALLOC_CMAKE_COMMAND}
make
