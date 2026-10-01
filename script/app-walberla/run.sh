#!/bin/bash

set -e

if [[ -z "${MLC_WALBERLA_SRC_PATH}" ]]; then
    echo "waLBerla source not found!"
    exit 1
fi

SRC="${MLC_WALBERLA_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
cmake -S . -B build
cmake --build build -j"${CORES}"

echo "waLBerla build step completed."
