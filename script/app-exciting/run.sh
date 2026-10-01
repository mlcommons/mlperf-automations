#!/bin/bash

set -e

if [[ -z "${MLC_EXCITING_SRC_PATH}" ]]; then
    echo "exciting source not found!"
    exit 1
fi

SRC="${MLC_EXCITING_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
make -j"${CORES}"

echo "exciting build step completed."
