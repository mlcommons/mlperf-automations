#!/bin/bash

set -e

if [[ -z "${MLC_PICONGPU_SRC_PATH}" ]]; then
    echo "PIConGPU source not found!"
    exit 1
fi

SRC="${MLC_PICONGPU_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
echo "Use pic-build / pic-create in ${SRC}/bin"

echo "PIConGPU build step completed."
