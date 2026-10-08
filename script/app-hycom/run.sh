#!/bin/bash

set -e

if [[ -z "${MLC_HYCOM_SRC_PATH}" ]]; then
    echo "HYCOM source not found!"
    exit 1
fi

SRC="${MLC_HYCOM_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
export ARCH=intelGF-impi-sm-relo
make ARCH=${ARCH}

echo "HYCOM build step completed."
