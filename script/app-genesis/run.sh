#!/bin/bash

set -e

if [[ -z "${MLC_GENESIS_SRC_PATH}" ]]; then
    echo "GENESIS source not found!"
    exit 1
fi

SRC="${MLC_GENESIS_SRC_PATH}"
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
INSTALL_DIR="${SRC}/install-${COMPILER_TAG}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}"
[ -x ./configure ] || autoreconf -fi
./configure FC=mpif90 CC=mpicc --prefix="${INSTALL_DIR}"
make clean >/dev/null 2>&1 || true
make -j${CORES}
make install

echo "GENESIS build step completed."
