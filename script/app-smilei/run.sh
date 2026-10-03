#!/bin/bash

set -e

if [[ -z "${MLC_SMILEI_SRC_PATH}" ]]; then
    echo "Smilei source not found!"
    exit 1
fi

SRC="${MLC_SMILEI_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"

cd "${SRC}"
export HDF5_ROOT_DIR="/usr/lib/x86_64-linux-gnu/hdf5/openmpi"
export CXXFLAGS="${CXXFLAGS} -I/usr/include/hdf5/openmpi"
make clean >/dev/null 2>&1 || true
make -j"${CORES}"

if [[ ! -x smilei ]]; then
    echo "Smilei binary not built"
    exit 1
fi
mkdir -p "install-${COMPILER_TAG}/bin" && cp smilei "install-${COMPILER_TAG}/bin/smilei"

echo "Smilei build step completed."
