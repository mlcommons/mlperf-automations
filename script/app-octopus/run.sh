#!/bin/bash

set -e

if [[ -z "${MLC_OCTOPUS_SRC_PATH}" ]]; then
    echo "Octopus source not found!"
    exit 1
fi

SRC="${MLC_OCTOPUS_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"

cd "${SRC}"

[ -x ./configure ] || autoreconf -fi

# --- Preprocessing with GNU cpp -------------------------------------------
# Octopus's Fortran sources need BOTH C-style token pasting (e.g.
# "#define CNST(x) x ## _8", "#define yFNAME(x,y) x ## _ ## y") AND Fortran
# string concatenation "//" to survive the C preprocessing step:
#   * standard cpp    pastes ## but strips // as a C++ comment
#   * traditional-cpp preserves // but ignores the ## paste operator
# Traditional cpp instead pastes two tokens separated by an empty comment with
# no surrounding whitespace ("x/**/y" -> "xy"), so rewrite every " ## " paste
# operator in the Fortran sources/headers to the "/**/" idiom and use
# traditional mode, satisfying both requirements.  (config.h at the repo root
# is consumed by the C compiler and is deliberately left untouched.)
find src \( -name '*.F90' -o -name '*.h' \) -print0 | xargs -0 sed -i 's/ ## /\/\*\*\//g'
FCCPP="cpp -traditional-cpp -ffreestanding -P"

# gfortran >= 10 rejects the legacy argument mismatches in Octopus's bundled
# expokit; allow them.
FFLAGS="-O3 -fallow-argument-mismatch"
./configure --prefix="${INSTALL_DIR}" FC=mpif90 CC=mpicc FCCPP="${FCCPP}" \
    FCFLAGS="${FFLAGS}" FFLAGS="${FFLAGS}"
make clean >/dev/null 2>&1 || true
make
make install

echo "Octopus build step completed."
