#!/bin/bash

set -e

if [[ -z "${MLC_WARPX_SRC_PATH}" ]]; then
    echo "WarpX source not found!"
    exit 1
fi

SRC="${MLC_WARPX_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
BUILD_DIR="build-${COMPILER_TAG}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
# AMReX and PICSAR are fetched automatically by CMake. Serial OpenMP build.
rm -rf "${BUILD_DIR}"
cmake -S . -B "${BUILD_DIR}" -DWarpX_MPI=OFF -DWarpX_COMPUTE=OMP -DWarpX_PYTHON=OFF -DWarpX_APP=ON
cmake --build "${BUILD_DIR}" -j"${CORES}"

if ! ls ${BUILD_DIR}/bin/warpx* >/dev/null 2>&1; then
    echo "WarpX binary not built"
    exit 1
fi

echo "WarpX build step completed."
