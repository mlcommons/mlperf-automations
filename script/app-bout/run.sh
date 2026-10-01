#!/bin/bash

set -e

if [[ -z "${MLC_BOUT_SRC_PATH}" ]]; then
    echo "BOUT++ source not found!"
    exit 1
fi

SRC="${MLC_BOUT_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
# NetCDF is required by the core library; Python interface disabled.
cmake -S . -B build -DBOUT_USE_NETCDF=ON -DBOUT_ENABLE_PYTHON=OFF
cmake --build build -j"${CORES}"

if ! ls build/lib/libbout++.so* >/dev/null 2>&1; then
    echo "BOUT++ library not built"
    exit 1
fi

echo "BOUT++ build step completed."
