#!/bin/bash

set -e

if [[ -z "${MLC_OPENMC_SRC_PATH}" ]]; then
    echo "OpenMC source not found!"
    exit 1
fi

SRC="${MLC_OPENMC_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
# Submodules are already checked out by the git,repo dependency.
cmake -S . -B build -DGIT_SUBMODULE=OFF -DCMAKE_INSTALL_PREFIX="${SRC}/install"
cmake --build build -j"${CORES}"

if [[ ! -x build/bin/openmc ]]; then
    echo "OpenMC binary not built"
    exit 1
fi

echo "OpenMC build step completed."
