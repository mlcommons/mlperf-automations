#!/bin/bash

set -e

if [[ -z "${MLC_ROOT_SRC_PATH}" ]]; then
    echo "ROOT source not found!"
    exit 1
fi

SRC="${MLC_ROOT_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
# Minimal configuration keeps the build within CI limits.
cmake -S . -B build -Dminimal=ON -Dbuiltin_zlib=ON
cmake --build build -j"${CORES}"

if ! ls build/lib/libCore.so >/dev/null 2>&1; then
    echo "ROOT core library not built"
    exit 1
fi

echo "ROOT build step completed."
