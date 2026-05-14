#!/bin/bash

# Skip when user-provided library path is supplied (path.# variation)
if [[ "${MLC_AOCL_LIB_PATH_PROVIDED}" == "yes" ]]; then
    echo "User-provided library path mode - skipping build"
    exit 0
fi
# Skip build for binary download
if [[ "${MLC_AOCL_BINARY_DOWNLOAD}" == "yes" ]]; then
    echo "Binary download mode - skipping build"
    exit 0
fi


# Determine install prefix
AOCL_VERSION="${MLC_AOCL_BLIS_VERSION:-${MLC_GIT_CHECKOUT:-unknown}}"
if [[ -n "${MLC_OUTDIRNAME}" ]]; then
    INSTALL_PREFIX="${MLC_OUTDIRNAME}/aocl-blis/${AOCL_VERSION}"
else
    INSTALL_PREFIX="${MLC_AOCL_BLIS_SRC_PATH}/install"
fi
if [[ -z ${MLC_AOCL_BLIS_SRC_PATH} ]]; then
    echo "Git repository not found!"
    exit 1
fi

cd ${MLC_AOCL_BLIS_SRC_PATH}

./configure \
    --prefix=${INSTALL_PREFIX} \
    --enable-threading=openmp \
    --enable-cblas \
    auto
test $? -eq 0 || exit $?

make -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
test $? -eq 0 || exit $?

make install
test $? -eq 0 || exit $?

echo "get-lib-aocl-blis built and installed successfully."
