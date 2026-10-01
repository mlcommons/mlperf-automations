#!/bin/bash

set -e

if [[ -z "${MLC_PENCIL_SRC_PATH}" ]]; then
    echo "Pencil Code source not found!"
    exit 1
fi

SRC="${MLC_PENCIL_SRC_PATH}"

cd "${SRC}"
export PENCIL_HOME="${SRC}"
# sourceme sets PATH to include the pc_* build helpers.
. "${SRC}/sourceme.sh" || true

# Build a representative sample with the GNU + MPI configuration.
cd samples/conv-slab
pc_build -f GNU-GCC_MPI

if [[ ! -x src/run.x ]]; then
    echo "Pencil Code binary not built"
    exit 1
fi

echo "Pencil Code build step completed."
