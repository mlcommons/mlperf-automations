#!/bin/bash

set -e

if [[ -z "${MLC_GRID_SRC_PATH}" ]]; then
    echo "Grid source not found!"
    exit 1
fi

SRC="${MLC_GRID_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true

# bootstrap.sh fetches Eigen; the pinned Bitbucket URL is dead, so point it at
# the current GitLab mirror before running it.
sed -i 's#http://bitbucket.org/eigen/eigen/get/3.3.3.tar.bz2#https://gitlab.com/libeigen/eigen/-/archive/3.3.7/eigen-3.3.7.tar.bz2#' bootstrap.sh
./bootstrap.sh

mkdir -p build
cd build
../configure --enable-comms=none --enable-simd=GEN --enable-doxygen-doc=no
# version.h is a generated (git-derived) header required by the library.
make version.h
make -j"${CORES}" -C lib

if [[ ! -f lib/libGrid.a ]]; then
    echo "Grid library not built"
    exit 1
fi

echo "Grid build step completed."
