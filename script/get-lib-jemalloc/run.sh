#!/bin/bash

set -e

#Add your run commands here...
# run "$MLC_RUN_CMD"
cd ${MLC_JEMALLOC_SRC_PATH}
autoconf
cd - 
mkdir -p obj
cd obj
echo "${MLC_JEMALLOC_CONFIGURE_COMMAND}"
${MLC_JEMALLOC_CONFIGURE_COMMAND}
${MLC_JEMALLOC_SRC_PATH}/configure --enable-autogen
make
