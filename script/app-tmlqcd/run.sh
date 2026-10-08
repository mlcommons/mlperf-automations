#!/bin/bash

set -e

if [[ -z "${MLC_TMLQCD_SRC_PATH}" ]]; then
    echo "tmLQCD source not found!"
    exit 1
fi

SRC="${MLC_TMLQCD_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
autoconf
./configure --disable-mpi CC=gcc FC=gfortran
make -j"${CORES}"

echo "tmLQCD build step completed."
