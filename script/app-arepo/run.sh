#!/bin/bash

set -e

if [[ -z "${MLC_AREPO_SRC_PATH}" ]]; then
    echo "AREPO source not found!"
    exit 1
fi

SRC="${MLC_AREPO_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
cp Template-Config.sh Config.sh
make -j"${CORES}"

echo "AREPO build step completed."
