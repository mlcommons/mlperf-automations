#!/bin/bash

set -e

if [[ -z "${MLC_MITGCM_SRC_PATH}" ]]; then
    echo "MITgcm source not found!"
    exit 1
fi

SRC="${MLC_MITGCM_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
case "${COMPILER_TAG}" in oneapi) MOPT=linux_amd64_ifort ;; *) MOPT=linux_amd64_gfortran ;; esac
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}/verification/tutorial_barotropic_gyre"
BUILD_SUB="build-${COMPILER_TAG}"
rm -rf "${BUILD_SUB}"; mkdir -p "${BUILD_SUB}" && cd "${BUILD_SUB}"
../../../tools/genmake2 -mods=../code -optfile=../../../tools/build_options/${MOPT}
make depend
make -j${CORES}

echo "MITgcm build step completed."
