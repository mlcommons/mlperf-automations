#!/bin/bash

set -e

if [[ -z "${MLC_GROMACS_SRC_PATH}" ]]; then
    echo "GROMACS source not found!"
    exit 1
fi

SRC="${MLC_GROMACS_SRC_PATH}"
BUILD_DIR="${SRC}/build"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

echo "Building GROMACS..."
echo "Source: ${SRC}"
echo "Build directory: ${BUILD_DIR}"

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

cmake "${SRC}" \
    -DGMX_MPI=ON \
    -DGMX_OPENMP=ON \
    -DGMX_FFT_LIBRARY=fftw3 \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
    -DGMX_BUILD_OWN_FFTW=OFF

echo "Building GROMACS with ${CORES} cores..."
cmake --build . -j${CORES}

echo "Installing GROMACS..."
cmake --install .

echo "GROMACS built successfully."
