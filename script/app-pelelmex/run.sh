#!/bin/bash

set -e

if [[ -z "${MLC_PELELMEX_SRC_PATH}" ]]; then
    echo "PeleLMeX source not found!"
    exit 1
fi

SRC="${MLC_PELELMEX_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
cmake -S . -B build -DPELE_ENABLE_MPI=OFF
cmake --build build -j"${CORES}"

echo "PeleLMeX build step completed."
