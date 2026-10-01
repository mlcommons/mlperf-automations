#!/bin/bash

set -e

if [[ -z "${MLC_SIESTA_SRC_PATH}" ]]; then
    echo "SIESTA source not found!"
    exit 1
fi

SRC="${MLC_SIESTA_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}/Obj"
sh ../Src/obj_setup.sh

# SIESTA 4.x uses an arch.make (no ./configure). Use the gfortran template.
ARCH_TEMPLATE="$(find .. -name gfortran.make | head -1)"
cp "${ARCH_TEMPLATE}" arch.make

# gfortran >= 10 rejects legacy argument mismatches in the MPI interface code.
echo 'FFLAGS += -fallow-argument-mismatch' >> arch.make

echo "Building SIESTA (serial, gfortran)..."
make

if [[ ! -x siesta ]]; then
    echo "SIESTA binary not built"
    exit 1
fi

echo "SIESTA build step completed."
