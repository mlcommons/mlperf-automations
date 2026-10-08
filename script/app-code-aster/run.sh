#!/bin/bash

set -e

if [[ -z "${MLC_CODE_ASTER_SRC_PATH}" ]]; then
    echo "Code_Aster source not found!"
    exit 1
fi

SRC="${MLC_CODE_ASTER_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
./configure
make -j"${CORES}"

echo "Code_Aster build step completed."
