#!/bin/bash

set -e

if [[ -z "${MLC_GIZMO_SRC_PATH}" ]]; then
    echo "GIZMO source not found!"
    exit 1
fi

SRC="${MLC_GIZMO_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
cp Template_Config.sh Config.sh
make -j"${CORES}"

echo "GIZMO build step completed."
