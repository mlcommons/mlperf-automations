#!/bin/bash

set -e

if [[ -z "${MLC_MFEM_SRC_PATH}" ]]; then
    echo "MFEM source not found!"
    exit 1
fi

SRC="${MLC_MFEM_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
# Serial build with the bundled dependencies (no external libraries required).
make serial -j"${CORES}"

if [[ ! -f libmfem.a ]]; then
    echo "MFEM library not built"
    exit 1
fi

# Build a representative example to confirm the library links.
make -C examples ex1 -j"${CORES}" || true

echo "MFEM build step completed."
