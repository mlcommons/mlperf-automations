#!/bin/bash

set -e

if [[ -z "${MLC_STAR_SRC_PATH}" ]]; then
    echo "STAR source not found!"
    exit 1
fi

SRC="${MLC_STAR_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}/source"
make -j"${CORES}" STAR CXX=g++

if [[ ! -x STAR ]]; then
    echo "STAR binary not built"
    exit 1
fi

echo "STAR build step completed."
