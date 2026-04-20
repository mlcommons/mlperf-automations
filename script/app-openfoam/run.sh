#!/bin/bash

set -e

if [[ -z "${MLC_OPENFOAM_SRC_PATH}" ]]; then
    echo "OpenFOAM source not found!"
    exit 1
fi

OPENFOAM_SRC="${MLC_OPENFOAM_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

echo "Building OpenFOAM from: ${OPENFOAM_SRC}"

cd "${OPENFOAM_SRC}"

# Source the OpenFOAM environment
if [[ -f etc/bashrc ]]; then
    source etc/bashrc || true
else
    echo "OpenFOAM etc/bashrc not found!"
    exit 1
fi

# Build OpenFOAM
echo "Building OpenFOAM with ${CORES} cores..."
./Allwmake -j${CORES} -s -q 2>&1 || ./Allwmake -j${CORES} 2>&1

echo "OpenFOAM built successfully."
