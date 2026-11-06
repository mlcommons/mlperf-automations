#!/bin/bash

set -e

if [[ -z "${MLC_OPENMM_SRC_PATH}" ]]; then
    echo "OpenMM source not found!"
    exit 1
fi

SRC="${MLC_OPENMM_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}"
mkdir -p build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
    -DOPENMM_BUILD_PYTHON_WRAPPERS=OFF -DOPENMM_BUILD_C_AND_FORTRAN_WRAPPERS=OFF
make -j${CORES}
make install

echo "OpenMM build step completed."
