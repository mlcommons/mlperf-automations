#!/bin/bash

set -e

if [[ -z "${MLC_PYSCF_SRC_PATH}" ]]; then
    echo "PySCF source not found!"
    exit 1
fi

SRC="${MLC_PYSCF_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}/pyscf/lib"
git config --global --add safe.directory "${SRC}" || true
mkdir -p build && cd build
cmake ..
cmake --build . -j"${CORES}"

echo "PySCF build step completed."
