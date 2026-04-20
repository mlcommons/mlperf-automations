#!/bin/bash

set -e

if [[ -z "${MLC_HMMER_SRC_PATH}" ]]; then
    echo "HMMER source not found!"
    exit 1
fi

SRC="${MLC_HMMER_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

echo "Building HMMER..."
echo "Source: ${SRC}"

cd "${SRC}"

# HMMER requires the Easel library to be cloned inside the source tree
if [[ ! -d easel ]]; then
    echo "Cloning Easel library..."
    git clone https://github.com/EddyRivasLab/easel
fi

# HMMER uses autoconf
if [[ ! -f configure ]]; then
    autoconf
fi

# Configure with MPI support
./configure --prefix="${INSTALL_DIR}" --enable-mpi CC=mpicc

echo "Building HMMER with ${CORES} cores..."
make -j${CORES}

echo "Installing HMMER..."
make install

echo "HMMER built successfully."
