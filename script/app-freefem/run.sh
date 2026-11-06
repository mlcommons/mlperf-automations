#!/bin/bash

set -e

if [[ -z "${MLC_FREEFEM_SRC_PATH}" ]]; then
    echo "FreeFEM source not found!"
    exit 1
fi

SRC="${MLC_FREEFEM_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
autoreconf -i
./configure --enable-download --without-mpi
make -j"${CORES}"

echo "FreeFEM build step completed."
