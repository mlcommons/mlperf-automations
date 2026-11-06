#!/bin/bash

set -e

if [[ -z "${MLC_QMCPACK_SRC_PATH}" ]]; then
    echo "QMCPACK source not found!"
    exit 1
fi

SRC="${MLC_QMCPACK_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}"
mkdir -p build && cd build
cmake ..
make -j${CORES}

echo "QMCPACK build step completed."
