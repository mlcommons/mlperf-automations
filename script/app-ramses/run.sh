#!/bin/bash

set -e

if [[ -z "${MLC_RAMSES_SRC_PATH}" ]]; then
    echo "RAMSES source not found!"
    exit 1
fi

SRC="${MLC_RAMSES_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}/bin"

# Default Makefile builds a serial (MPI=0), 1D (NDIM=1) hydro executable
# named ramses1d using the GNU (gfortran) compiler.
# RAMSES Makefile has no parallel dependency ordering (races on .mod
# files), so build serially.
echo "Building RAMSES (serial, 1D hydro)..."
make

if [[ ! -x ramses1d ]]; then
    echo "RAMSES binary (ramses1d) not built"
    exit 1
fi

echo "RAMSES built successfully."
