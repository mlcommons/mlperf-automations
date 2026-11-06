#!/bin/bash

set -e

if [[ -z "${MLC_DOLFINX_SRC_PATH}" ]]; then
    echo "DOLFINx source not found!"
    exit 1
fi

SRC="${MLC_DOLFINX_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}/cpp"
cmake -S . -B build
cmake --build build -j"${CORES}"

echo "DOLFINx build step completed."
