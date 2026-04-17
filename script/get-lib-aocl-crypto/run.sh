#!/bin/bash
if [[ -z ${MLC_AOCL_CRYPTO_SRC_PATH} ]]; then
    echo "Git repository not found!"
    exit 1
fi

cd ${MLC_AOCL_CRYPTO_SRC_PATH}
mkdir -p build && cd build

# Derive OpenSSL install prefix from the detected bin path
OPENSSL_ROOT=""
if [[ -n ${MLC_OPENSSL_INSTALLED_PATH} ]]; then
    OPENSSL_ROOT=$(dirname ${MLC_OPENSSL_INSTALLED_PATH})
fi

cmake .. \
    -DCMAKE_INSTALL_PREFIX=${MLC_AOCL_CRYPTO_SRC_PATH}/install \
    -DCMAKE_BUILD_TYPE=Release \
    ${OPENSSL_ROOT:+-DOPENSSL_INSTALL_DIR=${OPENSSL_ROOT}} \
    ${MLC_CMAKE_EXTRA_FLAGS}
test $? -eq 0 || exit $?

cmake --build . -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
test $? -eq 0 || exit $?

cmake --install .
test $? -eq 0 || exit $?

echo "get-lib-aocl-crypto built and installed successfully."
