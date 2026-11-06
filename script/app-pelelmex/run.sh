#!/bin/bash

set -e

if [[ -z "${MLC_PELELMEX_SRC_PATH}" ]]; then
    echo "PeleLMeX source not found!"
    exit 1
fi

SRC="${MLC_PELELMEX_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
BUILD_DIR="build-${COMPILER_TAG}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
rm -rf "${BUILD_DIR}"
cmake -S . -B "${BUILD_DIR}" -DPELE_ENABLE_MPI=OFF
cmake --build "${BUILD_DIR}" -j"${CORES}"

echo "PeleLMeX build step completed."
