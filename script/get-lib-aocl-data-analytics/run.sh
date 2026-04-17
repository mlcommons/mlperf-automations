#!/bin/bash
# Skip build for binary download
if [[ "${MLC_AOCL_BINARY_DOWNLOAD}" == "yes" ]]; then
    echo "Binary download mode - skipping build"
    exit 0
fi

if [[ -z ${MLC_AOCL_DA_SRC_PATH} ]]; then
    echo "Git repository not found!"
    exit 1
fi

cd ${MLC_AOCL_DA_SRC_PATH}

# Create a unified AOCL root with flat lib_LP64 / include_LP64 layout
AOCL_ROOT=${MLC_AOCL_DA_SRC_PATH}/aocl_root
rm -rf ${AOCL_ROOT} build
mkdir -p ${AOCL_ROOT}/lib_LP64 ${AOCL_ROOT}/include_LP64

# Symlink BLIS libraries and headers
if [[ -n ${MLC_AOCL_BLIS_INSTALL_PATH} ]]; then
    ln -sf ${MLC_AOCL_BLIS_INSTALL_PATH}/lib/libblis* ${AOCL_ROOT}/lib_LP64/
    ln -sf ${MLC_AOCL_BLIS_INSTALL_PATH}/include/blis ${AOCL_ROOT}/include_LP64/blis
    [[ -f ${MLC_AOCL_BLIS_INSTALL_PATH}/include/blis/cblas.h ]] && \
        ln -sf ${MLC_AOCL_BLIS_INSTALL_PATH}/include/blis/cblas.h ${AOCL_ROOT}/include_LP64/
    [[ -f ${MLC_AOCL_BLIS_INSTALL_PATH}/include/blis/blis.h ]] && \
        ln -sf ${MLC_AOCL_BLIS_INSTALL_PATH}/include/blis/blis.h ${AOCL_ROOT}/include_LP64/
fi

# Symlink libflame libraries and headers
if [[ -n ${MLC_AOCL_LIBFLAME_INSTALL_PATH} ]]; then
    ln -sf ${MLC_AOCL_LIBFLAME_INSTALL_PATH}/lib/libflame* ${AOCL_ROOT}/lib_LP64/
    for h in ${MLC_AOCL_LIBFLAME_INSTALL_PATH}/include/*.h ${MLC_AOCL_LIBFLAME_INSTALL_PATH}/include/*.hh; do
        [[ -f $h ]] && ln -sf $h ${AOCL_ROOT}/include_LP64/
    done
fi

# Symlink aocl-utils libraries and headers
if [[ -n ${MLC_AOCL_UTILS_INSTALL_PATH} ]]; then
    ln -sf ${MLC_AOCL_UTILS_INSTALL_PATH}/lib/libaoclutils* ${AOCL_ROOT}/lib_LP64/
    ln -sf ${MLC_AOCL_UTILS_INSTALL_PATH}/lib/libau_cpuid* ${AOCL_ROOT}/lib_LP64/ 2>/dev/null
    for h in ${MLC_AOCL_UTILS_INSTALL_PATH}/include/*; do
        [[ -e $h ]] && ln -sf $h ${AOCL_ROOT}/include_LP64/
    done
fi

# Symlink aocl-sparse if available
if [[ -n ${MLC_AOCL_SPARSE_INSTALL_PATH} ]]; then
    ln -sf ${MLC_AOCL_SPARSE_INSTALL_PATH}/lib/libaoclsparse* ${AOCL_ROOT}/lib_LP64/
    for h in ${MLC_AOCL_SPARSE_INSTALL_PATH}/include/*.h ${MLC_AOCL_SPARSE_INSTALL_PATH}/include/*.hpp; do
        [[ -f $h ]] && ln -sf $h ${AOCL_ROOT}/include_LP64/
    done
fi

mkdir -p build && cd build

export AOCL_ROOT=${AOCL_ROOT}
cmake .. \
    -DCMAKE_INSTALL_PREFIX=${MLC_AOCL_DA_SRC_PATH}/install \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_AOCL_ROOT=${AOCL_ROOT} \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_TESTS=OFF \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_DOC=OFF \
    -DCMAKE_POLICY_DEFAULT_CMP0167=OLD \
    ${MLC_CMAKE_EXTRA_FLAGS}
test $? -eq 0 || exit $?

cmake --build . -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
test $? -eq 0 || exit $?

cmake --install .
test $? -eq 0 || exit $?

echo "get-lib-aocl-data-analytics built and installed successfully."
