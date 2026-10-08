#!/bin/bash

set -e

if [[ -z "${MLC_HMMER_SRC_PATH}" ]]; then
    echo "HMMER source not found!"
    exit 1
fi

SRC="${MLC_HMMER_SRC_PATH}"
# Isolate the build per compiler so different toolchains do not clobber each other.
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
INSTALL_DIR="${SRC}/install-${COMPILER_TAG}"
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

# Configure with MPI support. mpicc/mpifort pick the underlying compiler from
# OMPI_CC/OMPI_FC exported by get-compiler-paths-amd for the selected family.
./configure --prefix="${INSTALL_DIR}" --enable-mpi CC=mpicc

# Force recompile so object files from another compiler are not reused (keeps
# autotools auxiliary files, unlike distclean).
make clean >/dev/null 2>&1 || true

echo "Building HMMER (${COMPILER_TAG}) with ${CORES} cores..."
make -j${CORES}

echo "Installing HMMER..."
make install

echo "HMMER built successfully."
