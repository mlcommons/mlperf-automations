#!/bin/bash

set -e

if [[ -z "${MLC_CODE_SATURNE_SRC_PATH}" ]]; then
    echo "code_saturne source not found!"
    exit 1
fi

SRC="${MLC_CODE_SATURNE_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}"
./sbin/bootstrap
./configure --prefix="${INSTALL_DIR}" --disable-gui --without-med
make -j${CORES}
make install

echo "code_saturne build step completed."
