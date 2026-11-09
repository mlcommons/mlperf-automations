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

if [[ -z ${MLC_AOCL_LIBFLAME_SRC_PATH} ]]; then
    echo "Git repository not found!"
    exit 1
fi

# Determine install prefix
AOCL_VERSION="${MLC_AOCL_LIBFLAME_VERSION:-${MLC_GIT_CHECKOUT:-unknown}}"
if [[ -n "${MLC_OUTDIRNAME}" ]]; then
    INSTALL_PREFIX="${MLC_OUTDIRNAME}/aocl-libflame/${AOCL_VERSION}"
else
    INSTALL_PREFIX="${MLC_AOCL_LIBFLAME_SRC_PATH}/install"
fi
# libflame needs aoclutils (au_cpuid_*); link it into libflame.so so -lflame alone resolves.
AOCLUTILS_LIB=""
if [[ -n "${MLC_AOCL_UTILS_INSTALL_PATH}" ]]; then
    AOCLUTILS_LIB=$(ls "${MLC_AOCL_UTILS_INSTALL_PATH}"/lib*/libaoclutils.so 2>/dev/null | head -1)
fi

cd ${MLC_AOCL_LIBFLAME_SRC_PATH}
mkdir -p build && cd build

cmake .. \
    -DCMAKE_INSTALL_PREFIX=${INSTALL_PREFIX} \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_TEST=OFF \
    -DENABLE_AMD_FLAGS=ON \
    ${MLC_AOCL_UTILS_INSTALL_PATH:+-DLIBAOCLUTILS_INCLUDE_PATH=${MLC_AOCL_UTILS_INSTALL_PATH}/include} \
    ${AOCLUTILS_LIB:+-DLIBAOCLUTILS_LIBRARY_PATH=${AOCLUTILS_LIB}} \
    ${AOCLUTILS_LIB:+"-DCMAKE_SHARED_LINKER_FLAGS=-Wl,--no-as-needed ${AOCLUTILS_LIB} -Wl,-rpath,$(dirname ${AOCLUTILS_LIB})"} \
    ${MLC_CMAKE_EXTRA_FLAGS}
test $? -eq 0 || exit $?

cmake --build . -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
test $? -eq 0 || exit $?

cmake --install .
test $? -eq 0 || exit $?

echo "get-lib-aocl-libflame built and installed successfully."
