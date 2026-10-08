#!/bin/bash

set -e

if [[ -z "${MLC_XGC_SRC_PATH}" ]]; then
    echo "XGC source not found!"
    exit 1
fi

SRC="${MLC_XGC_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
make -j"${CORES}"

echo "XGC build step completed."
