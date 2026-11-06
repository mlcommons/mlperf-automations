#!/bin/bash

set -e

if [[ -z "${MLC_YAMBO_SRC_PATH}" ]]; then
    echo "Yambo source not found!"
    exit 1
fi

SRC="${MLC_YAMBO_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
# NOTE: a plain git checkout does not ship the bundled iotk/netcdf source
# archives under ./archive that the internal-library build step expects; a
# full build therefore needs the official release tarball or pre-installed
# IOTK. Recipe is provided as a best-effort starting point.
./configure FC=gfortran --enable-open-mp \
    --with-fft-path=/usr --with-netcdf-path=/usr --with-netcdff-path=/usr
make yambo -j"${CORES}"

echo "Yambo build step completed."
