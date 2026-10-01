#!/bin/bash

set -e

if [[ -z "${MLC_CASTRO_SRC_PATH}" ]]; then
    echo "Castro source not found!"
    exit 1
fi

SRC="${MLC_CASTRO_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

# Castro's Make.Castro invokes `python`; provide a shim if only python3 exists.
mkdir -p "${SRC}/.pybin"
if ! command -v python >/dev/null 2>&1; then
    ln -sf "$(command -v python3)" "${SRC}/.pybin/python"
fi
export PATH="${SRC}/.pybin:${PATH}"

# AMReX and Microphysics ship as git submodules under external/.
cd "${SRC}/Exec/hydro_tests/Sedov"
make -j"${CORES}" COMP=gnu USE_MPI=FALSE DIM=2 \
    AMREX_HOME="${SRC}/external/amrex" \
    MICROPHYSICS_HOME="${SRC}/external/Microphysics"

if ! ls *.ex >/dev/null 2>&1; then
    echo "Castro executable not built"
    exit 1
fi

echo "Castro build step completed."
