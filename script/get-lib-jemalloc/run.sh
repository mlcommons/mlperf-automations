#!/bin/bash

set -e

#Add your run commands here...
# run "$MLC_RUN_CMD"
cd ${MLC_JEMALLOC_SRC_PATH}
autoconf
cd - 
mkdir -p obj
cd obj
${MLC_JEMALLOC_SRC_PATH}/configure --enable-autogen
make
