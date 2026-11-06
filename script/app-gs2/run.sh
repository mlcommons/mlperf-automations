#!/bin/bash

set -e

if [[ -z "${MLC_GS2_SRC_PATH}" ]]; then
    echo "GS2 source not found!"
    exit 1
fi

SRC="${MLC_GS2_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
make -j"${CORES}" GK_SYSTEM=gnu_ubuntu

echo "GS2 build step completed."
