#!/bin/bash

set -e

if [[ -z "${MLC_OPENQCD_SRC_PATH}" ]]; then
    echo "openQCD source not found!"
    exit 1
fi

SRC="${MLC_OPENQCD_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
make -j"${CORES}"

echo "openQCD build step completed."
