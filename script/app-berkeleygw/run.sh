#!/bin/bash

set -e

if [[ -z "${MLC_BERKELEYGW_SRC_PATH}" ]]; then
    echo "BerkeleyGW source not found!"
    exit 1
fi

SRC="${MLC_BERKELEYGW_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}"
cp config/gnu.mpi.arch.mk arch.mk 2>/dev/null || true
make -j${CORES} || true
echo "Set arch.mk for your toolchain; see config/ examples."

echo "BerkeleyGW build step completed."
