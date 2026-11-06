#!/bin/bash

set -e

if [[ -z "${MLC_GPAW_SRC_PATH}" ]]; then
    echo "GPAW source not found!"
    exit 1
fi

SRC="${MLC_GPAW_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"

cd "${SRC}"

# GPAW's C sources include C++ headers (<algorithm>); compile them with g++,
# which treats .c files as C++ (gcc does not).
export CC=g++
export CXX=g++

"${PYTHON}" -m venv "${INSTALL_DIR}"
"${INSTALL_DIR}/bin/pip" install --upgrade pip numpy scipy ase
"${INSTALL_DIR}/bin/pip" install .

"${INSTALL_DIR}/bin/gpaw" --version

echo "GPAW build step completed."
