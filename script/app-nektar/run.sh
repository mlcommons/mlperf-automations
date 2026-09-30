#!/bin/bash

set -e

if [[ -z "${MLC_NEKTAR_SRC_PATH}" ]]; then
    echo "Nektar++ source not found!"
    exit 1
fi

SRC="${MLC_NEKTAR_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
cmake -S . -B build \
    -DNEKTAR_BUILD_SOLVERS=OFF -DNEKTAR_BUILD_DEMOS=ON \
    -DNEKTAR_BUILD_TESTS=OFF -DNEKTAR_BUILD_UNIT_TESTS=OFF \
    -DNEKTAR_BUILD_UTILITIES=OFF -DNEKTAR_USE_MPI=OFF
cmake --build build -j"${CORES}"

if ! ls build/library/LibUtilities/libLibUtilities.so* >/dev/null 2>&1; then
    echo "Nektar++ library not built"
    exit 1
fi

echo "Nektar++ build step completed."
