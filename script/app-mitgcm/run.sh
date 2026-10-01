#!/bin/bash

set -e

if [[ -z "${MLC_MITGCM_SRC_PATH}" ]]; then
    echo "MITgcm source not found!"
    exit 1
fi

SRC="${MLC_MITGCM_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}/verification/tutorial_barotropic_gyre"
mkdir -p build && cd build
../../../tools/genmake2 -mods=../code -optfile=../../../tools/build_options/linux_amd64_gfortran
make depend
make -j${CORES}

echo "MITgcm build step completed."
