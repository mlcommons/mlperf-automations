#!/bin/bash

set -e

if [[ -z "${MLC_PALABOS_SRC_PATH}" ]]; then
    echo "Palabos source not found!"
    exit 1
fi

SRC="${MLC_PALABOS_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
# Build a representative example against the Palabos library.
cd examples/showCases/cavity3d
cmake -S . -B build
cmake --build build -j"${CORES}"

if [[ ! -x cavity3d ]]; then
    echo "Palabos example binary not built"
    exit 1
fi

echo "Palabos build step completed."
