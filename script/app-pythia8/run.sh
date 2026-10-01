#!/bin/bash

set -e

if [[ -z "${MLC_PYTHIA8_SRC_PATH}" ]]; then
    echo "Pythia8 source not found!"
    exit 1
fi

SRC="${MLC_PYTHIA8_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
./configure
make -j"${CORES}"

echo "Pythia8 build step completed."
