#!/bin/bash

set -e

if [[ -z "${MLC_SWIFT_SRC_PATH}" ]]; then
    echo "SWIFT source not found!"
    exit 1
fi

SRC="${MLC_SWIFT_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
./autogen.sh
# Serial (non-MPI) build with HDF5 support.
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
INSTALL_DIR="${SRC}/install-${COMPILER_TAG}"
./configure --disable-mpi --with-hdf5 --prefix="${INSTALL_DIR}"
make clean >/dev/null 2>&1 || true
make -j"${CORES}"
make install

if [[ ! -x swift ]]; then
    echo "SWIFT binary not built"
    exit 1
fi

echo "SWIFT build step completed."
