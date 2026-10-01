#!/bin/bash

set -e

if [[ -z "${MLC_GTC_SRC_PATH}" ]]; then
    echo "GTC source not found!"
    exit 1
fi

SRC="${MLC_GTC_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
make -j"${CORES}"

echo "GTC build step completed."
