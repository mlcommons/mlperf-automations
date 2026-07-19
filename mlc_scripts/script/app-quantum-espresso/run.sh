#!/bin/bash

set -e

if [[ -z "${MLC_QE_SRC_PATH}" ]]; then
    echo "Quantum ESPRESSO source not found!"
    exit 1
fi

SRC="${MLC_QE_SRC_PATH}"
BUILD_DIR="${SRC}/build"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

echo "Building Quantum ESPRESSO..."
echo "Source: ${SRC}"
echo "Build directory: ${BUILD_DIR}"

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

cmake "${SRC}" \
    -DQE_ENABLE_MPI=ON \
    -DQE_ENABLE_OPENMP=ON \
    -DQE_ENABLE_SCALAPACK=OFF \
    -DQE_ENABLE_HDF5=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}"

echo "Building Quantum ESPRESSO with ${CORES} cores..."
cmake --build . -j${CORES}

echo "Installing Quantum ESPRESSO..."
cmake --install .

echo "Quantum ESPRESSO built successfully."
