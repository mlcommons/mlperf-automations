#!/bin/bash

set -e

if [[ -z "${MLC_OPENMOLCAS_SRC_PATH}" ]]; then
    echo "OpenMolcas source not found!"
    exit 1
fi

SRC="${MLC_OPENMOLCAS_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
cmake -S . -B build -DLINALG=OpenBLAS
cmake --build build -j"${CORES}"

echo "OpenMolcas build step completed."
