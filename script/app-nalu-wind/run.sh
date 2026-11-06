#!/bin/bash

set -e

if [[ -z "${MLC_NALU_WIND_SRC_PATH}" ]]; then
    echo "Nalu-Wind source not found!"
    exit 1
fi

SRC="${MLC_NALU_WIND_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
cmake -S . -B build -DENABLE_TESTS=OFF
cmake --build build -j"${CORES}"

echo "Nalu-Wind build step completed."
