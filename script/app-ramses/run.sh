#!/bin/bash

set -e

if [[ -z "${MLC_RAMSES_SRC_PATH}" ]]; then
    echo "RAMSES source not found!"
    exit 1
fi

SRC="${MLC_RAMSES_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
cd "${SRC}/bin"

# Default Makefile builds a serial (MPI=0), 1D (NDIM=1) hydro executable
# named ramses1d using the GNU (gfortran) compiler.
# RAMSES Makefile has no parallel dependency ordering (races on .mod
# files), so build serially.
echo "Building RAMSES (serial, 1D hydro, ${COMPILER_TAG})..."
make clean >/dev/null 2>&1 || true
make ${FC:+F90="${FC}"} ${FC:+FC="${FC}"}

if [[ ! -x ramses1d ]]; then
    echo "RAMSES binary (ramses1d) not built"
    exit 1
fi
mkdir -p "${SRC}/install-${COMPILER_TAG}/bin" && cp ramses1d "${SRC}/install-${COMPILER_TAG}/bin/"

echo "RAMSES built successfully."
