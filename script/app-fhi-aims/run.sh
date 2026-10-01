#!/bin/bash

set -e

if [[ -z "${MLC_FHI_AIMS_SRC_PATH}" ]]; then
    echo "FHI-aims source not found!"
    exit 1
fi

SRC="${MLC_FHI_AIMS_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
cmake -S . -B build
cmake --build build -j"${CORES}"

echo "FHI-aims build step completed."
