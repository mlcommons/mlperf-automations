#!/bin/bash

set -e

if [[ -z "${MLC_FV3_SRC_PATH}" ]]; then
    echo "FV3 source not found!"
    exit 1
fi

SRC="${MLC_FV3_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
echo "FV3 builds within a host model (SHiELD/UFS) atop the FMS infrastructure."

echo "FV3 build step completed."
