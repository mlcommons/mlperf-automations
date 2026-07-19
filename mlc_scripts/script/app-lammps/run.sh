#!/bin/bash

set -e

if [[ -z "${MLC_LAMMPS_SRC_PATH}" ]]; then
    echo "LAMMPS source not found!"
    exit 1
fi

SRC="${MLC_LAMMPS_SRC_PATH}"
BUILD_DIR="${SRC}/build"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

echo "Building LAMMPS..."
echo "Source: ${SRC}"
echo "Build directory: ${BUILD_DIR}"

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

cmake "${SRC}/cmake" \
    -DBUILD_MPI=ON \
    -DBUILD_OMP=ON \
    -DFFT=FFTW3 \
    -DPKG_INTEL=ON \
    -DPKG_OPENMP=ON \
    -DPKG_ASPHERE=ON \
    -DPKG_CLASS2=ON \
    -DPKG_EXTRA-DUMP=ON \
    -DPKG_OPT=ON \
    -DPKG_REPLICA=ON \
    -DPKG_GRANULAR=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}"

echo "Building LAMMPS with ${CORES} cores..."
cmake --build . -j${CORES}

echo "Installing LAMMPS..."
cmake --install .

echo "LAMMPS built successfully."
