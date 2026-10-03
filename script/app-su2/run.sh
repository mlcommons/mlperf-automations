#!/bin/bash

set -e

if [[ -z "${MLC_SU2_SRC_PATH}" ]]; then
    echo "SU2 source not found!"
    exit 1
fi

SRC="${MLC_SU2_SRC_PATH}"
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
INSTALL_DIR="${SRC}/install-${COMPILER_TAG}"
BUILD_DIR="build-${COMPILER_TAG}"
rm -rf "${BUILD_DIR}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"

cd "${SRC}"

# SU2 ships its own meson (in externals/); use the meson.py wrapper so no
# system meson / pip install is required. Build a lean serial SU2_CFD.
"${PYTHON}" meson.py "${BUILD_DIR}" --prefix="${INSTALL_DIR}" -Dwith-mpi=disabled
ninja -C "${BUILD_DIR}" install

echo "SU2 build step completed."
