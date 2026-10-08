#!/bin/bash

set -e

if [[ -z "${MLC_CLOVERLEAF_SRC_PATH}" ]]; then
    echo "CloverLeaf source not found!"
    exit 1
fi

SRC="${MLC_CLOVERLEAF_SRC_PATH}"
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
INSTALL_DIR="${SRC}/install-${COMPILER_TAG}"
case "${COMPILER_TAG}" in oneapi) CLV=INTEL ;; *) CLV=GNU ;; esac
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

echo "Building CloverLeaf-ref..."
echo "Source: ${SRC}"

cd "${SRC}"

# CloverLeaf-ref uses Makefile with MPI Fortran
make clean >/dev/null 2>&1 || true
make COMPILER=${CLV} MPI_COMPILER=mpif90 C_MPI_COMPILER=mpicc -j${CORES}

# Install binary
mkdir -p "${INSTALL_DIR}/bin"
cp clover_leaf "${INSTALL_DIR}/bin/"

echo "CloverLeaf-ref built successfully."
