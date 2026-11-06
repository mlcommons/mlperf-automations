#!/bin/bash

set -e

if [[ -z "${MLC_DFTBPLUS_SRC_PATH}" ]]; then
    echo "DFTB+ source not found!"
    exit 1
fi

SRC="${MLC_DFTBPLUS_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
cmake -B _build -DWITH_MPI=NO -DWITH_OMP=YES -DCMAKE_INSTALL_PREFIX="${SRC}/install"
cmake --build _build -- -j"${CORES}"

if [[ ! -x _build/app/dftb+/dftb+ ]]; then
    echo "DFTB+ binary not built"
    exit 1
fi

echo "DFTB+ build step completed."
