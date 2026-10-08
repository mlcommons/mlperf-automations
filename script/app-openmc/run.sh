#!/bin/bash

set -e

if [[ -z "${MLC_OPENMC_SRC_PATH}" ]]; then
    echo "OpenMC source not found!"
    exit 1
fi

SRC="${MLC_OPENMC_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
BUILD_DIR="build-${COMPILER_TAG}"

cd "${SRC}"
# Submodules are already checked out by the git,repo dependency.
rm -rf "${BUILD_DIR}"
cmake -S . -B "${BUILD_DIR}" -DGIT_SUBMODULE=OFF -DCMAKE_INSTALL_PREFIX="${SRC}/install"
cmake --build "${BUILD_DIR}" -j"${CORES}"

if [[ ! -x ${BUILD_DIR}/bin/openmc ]]; then
    echo "OpenMC binary not built"
    exit 1
fi

echo "OpenMC build step completed."
