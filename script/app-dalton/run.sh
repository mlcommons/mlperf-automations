#!/bin/bash

set -e

if [[ -z "${MLC_DALTON_SRC_PATH}" ]]; then
    echo "DALTON source not found!"
    exit 1
fi

SRC="${MLC_DALTON_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
# DALTON's setup driver invokes `python`; provide a shim if only python3 exists.
mkdir -p "${SRC}/.pybin"
if ! command -v python >/dev/null 2>&1; then
    ln -sf "$(command -v python3)" "${SRC}/.pybin/python"
fi
export PATH="${SRC}/.pybin:${PATH}"

./setup --fc=gfortran --cc=gcc --cxx=g++
cmake --build build -j"${CORES}"

if [[ ! -f build/dalton.x ]]; then
    echo "DALTON binary not built"
    exit 1
fi

echo "DALTON build step completed."
