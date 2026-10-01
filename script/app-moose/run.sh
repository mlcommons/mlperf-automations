#!/bin/bash

set -e

if [[ -z "${MLC_MOOSE_SRC_PATH}" ]]; then
    echo "MOOSE source not found!"
    exit 1
fi

SRC="${MLC_MOOSE_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
./scripts/update_and_rebuild_petsc.sh
./scripts/update_and_rebuild_libmesh.sh
make -j"${CORES}"

echo "MOOSE build step completed."
