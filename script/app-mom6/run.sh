#!/bin/bash

set -e

if [[ -z "${MLC_MOM6_SRC_PATH}" ]]; then
    echo "MOM6 source not found!"
    exit 1
fi

SRC="${MLC_MOM6_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

# gfortran >= 10 needs this for FMS/MOM6 legacy MPI interfaces.
export FCFLAGS="-fallow-argument-mismatch -O2"

# MOM6 ships tooling to fetch+build its dependencies (FMS, GSW, CVMix).
cd "${SRC}/ac/deps"
make -j${CORES}

# Configure and build the MOM6 ocean-only executable against those deps.
cd "${SRC}/ac"
autoreconf -i
./configure
make -j${CORES}

echo "MOM6 build step completed."
