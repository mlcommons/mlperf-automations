#!/bin/bash

set -e

# Skip when user-provided library path is supplied (path.# variation)
if [[ "${MLC_JEMALLOC_LIB_PATH_PROVIDED}" == "yes" ]]; then
    echo "User-provided library path mode - skipping build"
    exit 0
fi

cd ${MLC_JEMALLOC_SRC_PATH}
autoconf
cd - 

mkdir -p obj
cd obj

echo "${MLC_JEMALLOC_CONFIGURE_COMMAND}"
${MLC_JEMALLOC_CONFIGURE_COMMAND}

make
make install

rm -rf obj
