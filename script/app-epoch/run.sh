#!/bin/bash

set -e

if [[ -z "${MLC_EPOCH_SRC_PATH}" ]]; then
    echo "EPOCH source not found!"
    exit 1
fi

SRC="${MLC_EPOCH_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}/epoch2d"
make COMPILER=gfortran -j"${CORES}"

echo "EPOCH build step completed."
