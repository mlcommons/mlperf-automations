#!/bin/bash

set -e

if [[ -z "${MLC_NEK5000_SRC_PATH}" ]]; then
    echo "Nek5000 source not found!"
    exit 1
fi

SRC="${MLC_NEK5000_SRC_PATH}"

# Build the Nek5000 pre/post-processing tools (pure Fortran/C, no MPI required).
# This compiles the shared Nek5000 source and installs the tools into bin/.
cd "${SRC}/tools"
export FC="${FC:-gfortran}"
export CC="${CC:-gcc}"

echo "Building Nek5000 tools (genmap, genbox, n2to3)..."
for tool in genmap genbox n2to3; do
    ./maketools "${tool}"
done

if [[ ! -x "${SRC}/bin/genmap" ]]; then
    echo "Nek5000 tool (genmap) not built"
    exit 1
fi

echo "Nek5000 built successfully."
