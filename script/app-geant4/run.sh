#!/bin/bash

set -e

if [[ -z "${MLC_GEANT4_SRC_PATH}" ]]; then
    echo "Geant4 source not found!"
    exit 1
fi

SRC="${MLC_GEANT4_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
cmake -S . -B build \
    -DGEANT4_INSTALL_DATA=OFF \
    -DGEANT4_USE_SYSTEM_EXPAT=ON \
    -DGEANT4_BUILD_MULTITHREADED=OFF
cmake --build build -j"${CORES}"

if ! ls build/BuildProducts/lib/libG4global* >/dev/null 2>&1; then
    echo "Geant4 libraries not built"
    exit 1
fi

echo "Geant4 build step completed."
