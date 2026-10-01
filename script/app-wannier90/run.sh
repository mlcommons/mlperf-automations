#!/bin/bash

set -e

if [[ -z "${MLC_WANNIER90_SRC_PATH}" ]]; then
    echo "Wannier90 source not found!"
    exit 1
fi

SRC="${MLC_WANNIER90_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
cp config/make.inc.gfort make.inc
make -j"${CORES}"

echo "Wannier90 build step completed."
