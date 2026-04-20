#!/bin/bash

set -e

if [[ -z "${MLC_NAMD_SRC_PATH}" ]]; then
    echo "NAMD source not found!"
    exit 1
fi

SRC="${MLC_NAMD_SRC_PATH}"
BUILD_DIR="${SRC}/build"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

echo "Building NAMD..."
echo "Source: ${SRC}"
echo "Build directory: ${BUILD_DIR}"

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# NAMD 3.x uses CMake
cmake "${SRC}" \
    -DNAMD_ARCH=Linux-x86_64-g++ \
    -DNAMD_MPI=ON \
    -DNAMD_FFTW=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}"

echo "Building NAMD with ${CORES} cores..."
cmake --build . -j${CORES}

echo "Installing NAMD..."
cmake --install . || make install DESTDIR="${INSTALL_DIR}" || true

echo "NAMD built successfully."
