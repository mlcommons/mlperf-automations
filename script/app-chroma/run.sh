#!/bin/bash

set -e

if [[ -z "${MLC_CHROMA_SRC_PATH}" ]]; then
    echo "Chroma source not found!"
    exit 1
fi

SRC="${MLC_CHROMA_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
DEPS="${SRC}/deps"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

mkdir -p "${DEPS}"

# Chroma needs QDP++ (data-parallel layer). Build the scalar (single-node)
# variant so no QMP/MPI layer is required.
if [[ ! -d "${DEPS}/qdpxx" ]]; then
    git clone --depth 1 --recurse-submodules https://github.com/usqcd-software/qdpxx.git "${DEPS}/qdpxx"
fi
cd "${DEPS}/qdpxx"
./autogen.sh
./configure --prefix="${INSTALL_DIR}" --enable-parallel-arch=scalar \
    --enable-precision=double CXX=g++ CC=gcc
make -j${CORES}
make install

# Build Chroma against the scalar QDP++.
cd "${SRC}"
./autogen.sh
./configure --prefix="${INSTALL_DIR}" --with-qdp="${INSTALL_DIR}" CXX=g++ CC=gcc
make -j${CORES}
make install

echo "Chroma build step completed."
