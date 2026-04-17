#!/bin/bash
if [[ -z ${MLC_AOCL_BLIS_SRC_PATH} ]]; then
    echo "Git repository not found!"
    exit 1
fi

cd ${MLC_AOCL_BLIS_SRC_PATH}

./configure \
    --prefix=${MLC_AOCL_BLIS_SRC_PATH}/install \
    --enable-threading=openmp \
    --enable-cblas \
    auto
test $? -eq 0 || exit $?

make -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
test $? -eq 0 || exit $?

make install
test $? -eq 0 || exit $?

echo "get-lib-aocl-blis built and installed successfully."
