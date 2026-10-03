#!/bin/bash

set -e

if [[ -z "${MLC_EPOCH_SRC_PATH}" ]]; then
    echo "EPOCH source not found!"
    exit 1
fi

SRC="${MLC_EPOCH_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
case "${COMPILER_TAG}" in oneapi) EPC=intel ;; *) EPC=gfortran ;; esac

cd "${SRC}/epoch2d"
make clean >/dev/null 2>&1 || true
make COMPILER=${EPC} -j"${CORES}"
mkdir -p "${SRC}/install-${COMPILER_TAG}/bin" && cp bin/epoch2d "${SRC}/install-${COMPILER_TAG}/bin/"

echo "EPOCH build step completed."
