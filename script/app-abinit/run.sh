#!/bin/bash

set -e

if [[ -z "${MLC_ABINIT_SRC_PATH}" ]]; then
    echo "ABINIT source not found!"
    exit 1
fi

SRC="${MLC_ABINIT_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

# ABINIT build scripts invoke `python`; ensure it resolves to python3.
if ! command -v python >/dev/null 2>&1; then
    SHIM_DIR="$(mktemp -d)"
    ln -sf "$(command -v "${PYTHON}" || command -v python3)" "${SHIM_DIR}/python"
    export PATH="${SHIM_DIR}:${PATH}"
fi

cd "${SRC}"
[ -x ./configure ] || ./config/scripts/makemake
./configure --prefix="${INSTALL_DIR}" FC=mpif90 CC=mpicc
make -j${CORES}
make install

echo "ABINIT build step completed."
