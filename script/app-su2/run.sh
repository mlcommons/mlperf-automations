#!/bin/bash

set -e

if [[ -z "${MLC_SU2_SRC_PATH}" ]]; then
    echo "SU2 source not found!"
    exit 1
fi

SRC="${MLC_SU2_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"

cd "${SRC}"

# SU2 ships its own meson (in externals/); use the meson.py wrapper so no
# system meson / pip install is required. Build a lean serial SU2_CFD.
"${PYTHON}" meson.py build --prefix="${INSTALL_DIR}" -Dwith-mpi=disabled
ninja -C build install

echo "SU2 build step completed."
