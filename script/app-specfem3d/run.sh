#!/bin/bash

set -e

if [[ -z "${MLC_SPECFEM3D_SRC_PATH}" ]]; then
    echo "SPECFEM3D source not found!"
    exit 1
fi

SRC="${MLC_SPECFEM3D_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"

echo "Configuring SPECFEM3D (serial, no MPI)..."
./configure --without-mpi FC=gfortran CC=gcc

echo "Building SPECFEM3D with ${CORES} cores..."
make -j${CORES}

if [[ ! -x bin/xspecfem3D ]]; then
    echo "SPECFEM3D binary (xspecfem3D) not built"
    exit 1
fi

echo "SPECFEM3D built successfully."
