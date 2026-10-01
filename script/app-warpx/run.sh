#!/bin/bash

set -e

if [[ -z "${MLC_WARPX_SRC_PATH}" ]]; then
    echo "WarpX source not found!"
    exit 1
fi

SRC="${MLC_WARPX_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
# AMReX and PICSAR are fetched automatically by CMake. Serial OpenMP build.
cmake -S . -B build -DWarpX_MPI=OFF -DWarpX_COMPUTE=OMP -DWarpX_PYTHON=OFF -DWarpX_APP=ON
cmake --build build -j"${CORES}"

if ! ls build/bin/warpx* >/dev/null 2>&1; then
    echo "WarpX binary not built"
    exit 1
fi

echo "WarpX build step completed."
