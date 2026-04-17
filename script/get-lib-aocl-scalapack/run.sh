#!/bin/bash
# Skip build for binary download
if [[ "${MLC_AOCL_BINARY_DOWNLOAD}" == "yes" ]]; then
    echo "Binary download mode - skipping build"
    exit 0
fi

if [[ -z ${MLC_AOCL_SCALAPACK_SRC_PATH} ]]; then
    echo "Git repository not found!"
    exit 1
fi

cd ${MLC_AOCL_SCALAPACK_SRC_PATH}

# Create a unified AOCL root with symlinks for cmake discovery
AOCL_ROOT=${MLC_AOCL_SCALAPACK_SRC_PATH}/aocl_root
rm -rf ${AOCL_ROOT}
mkdir -p ${AOCL_ROOT}
[[ -n ${MLC_AOCL_BLIS_INSTALL_PATH} ]] && ln -sf ${MLC_AOCL_BLIS_INSTALL_PATH} ${AOCL_ROOT}/blis
[[ -n ${MLC_AOCL_UTILS_INSTALL_PATH} ]] && ln -sf ${MLC_AOCL_UTILS_INSTALL_PATH} ${AOCL_ROOT}/utils
[[ -n ${MLC_AOCL_LIBFLAME_INSTALL_PATH} ]] && ln -sf ${MLC_AOCL_LIBFLAME_INSTALL_PATH} ${AOCL_ROOT}/libflame

mkdir -p build && cd build

cmake .. \
    -DCMAKE_INSTALL_PREFIX=${MLC_AOCL_SCALAPACK_SRC_PATH}/install \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_AOCL_ROOT=${AOCL_ROOT} \
    ${MLC_CMAKE_EXTRA_FLAGS}
test $? -eq 0 || exit $?

cmake --build . -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
test $? -eq 0 || exit $?

cmake --install .
test $? -eq 0 || exit $?

echo "get-lib-aocl-scalapack built and installed successfully."
