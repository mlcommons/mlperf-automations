#!/bin/bash
if [[ -z ${MLC_AOCL_DLP_SRC_PATH} ]]; then
    echo "Git repository not found!"
    exit 1
fi

cd ${MLC_AOCL_DLP_SRC_PATH}
mkdir -p build && cd build

cmake .. \
    -DCMAKE_INSTALL_PREFIX=${MLC_AOCL_DLP_SRC_PATH}/install \
    -DCMAKE_BUILD_TYPE=Release \
    ${MLC_CMAKE_EXTRA_FLAGS}
test $? -eq 0 || exit $?

cmake --build . -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
test $? -eq 0 || exit $?

cmake --install .
test $? -eq 0 || exit $?

echo "get-lib-aocl-dlp built and installed successfully."
