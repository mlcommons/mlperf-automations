#!/bin/bash

set -e

if [[ -z "${MLC_VPIC_SRC_PATH}" ]]; then
    echo "VPIC source not found!"
    exit 1
fi

SRC="${MLC_VPIC_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
cmake -S . -B build -DENABLE_INTEGRATED_TESTS=OFF -DUSE_PTHREADS=OFF -DUSE_OPENMP=ON
cmake --build build -j"${CORES}"

echo "VPIC build step completed."
