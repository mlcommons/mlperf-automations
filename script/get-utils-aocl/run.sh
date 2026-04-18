#!/bin/bash
# Skip build for binary download
if [[ "${MLC_AOCL_BINARY_DOWNLOAD}" == "yes" ]]; then
    echo "Binary download mode - skipping build"
    exit 0
fi

if [[ -z ${MLC_AOCL_UTILS_SRC_PATH} ]]; then
    echo "Git repository not found!"
    exit 1
fi

cd ${MLC_AOCL_UTILS_SRC_PATH}
mkdir -p build && cd build

cmake .. \
    -DCMAKE_INSTALL_PREFIX=${MLC_AOCL_UTILS_SRC_PATH}/install \
    -DCMAKE_BUILD_TYPE=Release \
    ${MLC_CMAKE_EXTRA_FLAGS}
test $? -eq 0 || exit $?

cmake --build . -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
test $? -eq 0 || exit $?

cmake --install .
test $? -eq 0 || exit $?

echo "get-utils-aocl built and installed successfully."
