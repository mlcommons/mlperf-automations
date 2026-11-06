#!/bin/bash

set -e

if [[ -z "${MLC_DALTON_SRC_PATH}" ]]; then
    echo "DALTON source not found!"
    exit 1
fi

SRC="${MLC_DALTON_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
BUILD_DIR="build-${COMPILER_TAG}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
# DALTON's setup driver invokes `python`; provide a shim if only python3 exists.
mkdir -p "${SRC}/.pybin"
if ! command -v python >/dev/null 2>&1; then
    ln -sf "$(command -v python3)" "${SRC}/.pybin/python"
fi
export PATH="${SRC}/.pybin:${PATH}"

rm -rf "${BUILD_DIR}"
./setup --fc="${FC:-gfortran}" --cc="${CC:-gcc}" --cxx="${CXX:-g++}" "${BUILD_DIR}"
cmake --build "${BUILD_DIR}" -j"${CORES}"

if [[ ! -f "${BUILD_DIR}/dalton.x" ]]; then
    echo "DALTON binary not built"
    exit 1
fi

echo "DALTON build step completed."
