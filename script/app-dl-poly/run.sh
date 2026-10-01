#!/bin/bash

set -e

if [[ -z "${MLC_DL_POLY_SRC_PATH}" ]]; then
    echo "DL_POLY source not found!"
    exit 1
fi

SRC="${MLC_DL_POLY_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}"
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DWITH_MPI=ON
make -j${CORES}

echo "DL_POLY build step completed."
