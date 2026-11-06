#!/bin/bash

set -e

if [[ -z "${MLC_SHERPA_SRC_PATH}" ]]; then
    echo "Sherpa source not found!"
    exit 1
fi

SRC="${MLC_SHERPA_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
cmake -S . -B build \
    -DSHERPA_ENABLE_MPI=OFF -DSHERPA_ENABLE_INSTALL_LIBZIP=ON \
    -DSHERPA_ENABLE_LHAPDF=OFF -DSHERPA_ENABLE_HEPMC3=OFF \
    -DSHERPA_ENABLE_RIVET=OFF -DSHERPA_ENABLE_FASTJET=OFF
cmake --build build -j"${CORES}"

if ! find build -name "libSherpaMain*" | grep -q .; then
    echo "Sherpa library not built"
    exit 1
fi

echo "Sherpa build step completed."
