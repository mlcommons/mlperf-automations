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

# Locate BLIS and libflame libraries
# Binary installs have LP64/ILP64 subdirectories; source builds are flat
BLIS_LIB=$(find ${MLC_AOCL_BLIS_LIB_PATH} -name "libblis-mt.so" -path "*/LP64/*" 2>/dev/null | head -1)
if [[ -z "${BLIS_LIB}" ]]; then
    BLIS_LIB=$(find ${MLC_AOCL_BLIS_LIB_PATH} -name "libblis-mt.so" 2>/dev/null | head -1)
fi
if [[ -z "${BLIS_LIB}" ]]; then
    BLIS_LIB=$(find ${MLC_AOCL_BLIS_LIB_PATH} -name "libblis-mt.a" 2>/dev/null | head -1)
fi
if [[ -z "${BLIS_LIB}" ]]; then
    BLIS_LIB=$(find ${MLC_AOCL_BLIS_LIB_PATH} -name "libblis.so" 2>/dev/null | head -1)
fi

FLAME_LIB=$(find ${MLC_AOCL_LIBFLAME_LIB_PATH} -name "libflame.so" 2>/dev/null | head -1)
if [[ -z "${FLAME_LIB}" ]]; then
    FLAME_LIB=$(find ${MLC_AOCL_LIBFLAME_LIB_PATH} -name "libflame.a" 2>/dev/null | head -1)
fi

echo "BLIS library: ${BLIS_LIB}"
echo "FLAME library: ${FLAME_LIB}"

# Clean previous build
rm -rf build
mkdir -p build && cd build

cmake .. \
    -DCMAKE_INSTALL_PREFIX=${MLC_AOCL_SCALAPACK_SRC_PATH}/install \
    -DCMAKE_BUILD_TYPE=Release \
    -DBLAS_LIBRARIES="${BLIS_LIB}" \
    -DLAPACK_LIBRARIES="${FLAME_LIB};${BLIS_LIB};-lm;-lpthread;-lgfortran" \
    -DSCALAPACK_BUILD_TESTS=OFF \
    ${MLC_CMAKE_EXTRA_FLAGS}
test $? -eq 0 || exit $?

# Build only the scalapack target (avoid parallel LAPACK ExternalProject issues)
cmake --build . --target scalapack -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
test $? -eq 0 || exit $?

# Manual install to avoid cmake trying to install non-existent reference LAPACK/BLAS
mkdir -p ${MLC_AOCL_SCALAPACK_SRC_PATH}/install/lib
cp -f lib/libscalapack.a ${MLC_AOCL_SCALAPACK_SRC_PATH}/install/lib/
# Also copy shared lib if built
cp -f lib/libscalapack.so* ${MLC_AOCL_SCALAPACK_SRC_PATH}/install/lib/ 2>/dev/null || true

echo "get-lib-aocl-scalapack built and installed successfully."
