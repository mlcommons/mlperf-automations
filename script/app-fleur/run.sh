#!/bin/bash

set -e

if [[ -z "${MLC_FLEUR_SRC_PATH}" ]]; then
    echo "FLEUR source not found!"
    exit 1
fi

SRC="${MLC_FLEUR_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"

# configure.sh generates a build.<compiler> directory and a CMake build there.
./configure.sh -l gfortran
BUILD_DIR="$(ls -d build.gfortran build.* build 2>/dev/null | head -1)"
cd "${BUILD_DIR}"
make -j${CORES}

echo "FLEUR build step completed."
