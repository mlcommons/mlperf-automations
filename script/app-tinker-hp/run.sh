#!/bin/bash

set -e

if [[ -z "${MLC_TINKER_HP_SRC_PATH}" ]]; then
    echo "Tinker-HP source not found!"
    exit 1
fi

SRC="${MLC_TINKER_HP_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"

# Tinker-HP (v1.3/CPU) is written for the Intel toolchain: its Fortran sources
# (e.g. domdecstuff.f90) use ifort-specific constructs and its BLAS path expects
# Intel MKL. A full Intel oneAPI (ifx/ifort + Intel MPI + MKL) is therefore
# required; source it if available.
for v in /opt/intel/oneapi/setvars.sh; do
    [ -f "$v" ] && source "$v" >/dev/null 2>&1 || true
done

# configure invokes `python`; ensure it resolves to python3.
if ! command -v python >/dev/null 2>&1; then
    SHIM_DIR="$(mktemp -d)"
    ln -sf "$(command -v "${PYTHON}" || command -v python3)" "${SHIM_DIR}/python"
    export PATH="${SHIM_DIR}:${PATH}"
fi

cd "${SRC}/v1.3/CPU"

# Prefer the Intel MPI Fortran wrapper (ifx/ifort) when oneAPI is present.
if command -v mpiifort >/dev/null 2>&1; then
    TFC=mpiifort
else
    TFC=mpif90
fi

autoreconf -fi
./configure FC="${TFC}" F77="${TFC}" --with-blaslib=mkl --enable-fft-generic \
    --disable-colvars --disable-plumed --disable-tcl
make -j${CORES} ACLOCAL=true AUTOMAKE=true AUTOCONF=true AUTOHEADER=true

echo "Tinker-HP build step completed."
