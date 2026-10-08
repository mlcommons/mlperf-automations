#!/bin/bash

set -e

if [[ -z "${MLC_CHARMM_SRC_PATH}" ]]; then
    echo "CHARMM source not found!"
    exit 1
fi

SRC="${MLC_CHARMM_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
./configure
make -j"${CORES}" -C build/cmake

echo "CHARMM build step completed."
