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
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
case "${COMPILER_TAG}" in gcc|default) CMP=gnu ;; oneapi) CMP=intel ;; *) CMP=llvm ;; esac
# AMReX names the binary with ${CMP}, so different compilers do not clobber.
# Override the actual compilers with the selected toolchain (gnu/llvm flag style).
make -j"${CORES}" COMP=${CMP} USE_MPI=FALSE DIM=2 \
    ${CXX:+CXX="${CXX}"} ${CC:+CC="${CC}"} ${FC:+FC="${FC}"} ${FC:+F90="${FC}"} \
    AMREX_HOME="${SRC}/external/amrex" \
    MICROPHYSICS_HOME="${SRC}/external/Microphysics"

if ! ls *.ex >/dev/null 2>&1; then
    echo "Castro executable not built"
    exit 1
fi
mkdir -p "${SRC}/install-${COMPILER_TAG}/bin"
cp "$(ls -t *.ex | head -1)" "${SRC}/install-${COMPILER_TAG}/bin/Castro.ex"

echo "Castro build step completed."
