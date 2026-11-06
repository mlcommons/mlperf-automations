#!/bin/bash

set -e

if [[ -z "${MLC_GAMER_SRC_PATH}" ]]; then
    echo "GAMER source not found!"
    exit 1
fi

SRC="${MLC_GAMER_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}/src"
git config --global --add safe.directory "${SRC}" || true
make -j"${CORES}"

echo "GAMER build step completed."
