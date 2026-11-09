#!/bin/bash

set -e

if [[ -z "${MLC_NWCHEM_SRC_PATH}" ]]; then
    echo "NWChem source not found!"
    exit 1
fi

NWCHEM_TOP="${MLC_NWCHEM_SRC_PATH}"
INSTALL_DIR="${NWCHEM_TOP}/install"

export NWCHEM_TOP
export NWCHEM_TARGET=LINUX64
export NWCHEM_MODULES="${MLC_NWCHEM_NWCHEM_MODULES:-all}"
export ARMCI_NETWORK="${MLC_NWCHEM_ARMCI_NETWORK:-MPI-PR}"

export USE_MPI=y
export USE_MPIF=y
export USE_MPIF4=y

# OpenMP support
if [[ "${MLC_NWCHEM_USE_OPENMP}" == "1" ]]; then
    export USE_OPENMP=1
fi

export BLAS_SIZE=4
export USE_64TO32=y
# BLAS/LAPACK from get,lib,blas-lapack: AOCL BLIS/libflame on x86_64, OpenBLAS elsewhere.
export BLASOPT="${MLC_BLAS_LIBS}"
export LAPACK_LIB="${MLC_LAPACK_LIBS}"
echo "BLASOPT=${BLASOPT}"
echo "LAPACK_LIB=${LAPACK_LIB}"

# ScaLAPACK - the AOCL build installs libscalapack under build/lib (or install/lib*),
# which is not always where MLC_AOCL_SCALAPACK_LIB_PATH points. Resolve the repo root
# with realpath -m (works even if the lib dir does not exist) and search for the lib.
if [[ -n "${MLC_AOCL_SCALAPACK_LIB_PATH}" ]]; then
    SP_ROOT=$(realpath -m "${MLC_AOCL_SCALAPACK_LIB_PATH}/../.." 2>/dev/null || echo "${MLC_AOCL_SCALAPACK_LIB_PATH}")
    SCALAPACK_LIB=$(find "${SP_ROOT}" "${MLC_AOCL_SCALAPACK_LIB_PATH}" \( -name "libscalapack.so" -o -name "libscalapack.a" \) 2>/dev/null | head -1)
    if [[ -n "${SCALAPACK_LIB}" ]]; then
        SCALAPACK_LIB_DIR=$(dirname "${SCALAPACK_LIB}")
    else
        SCALAPACK_LIB_DIR="${MLC_AOCL_SCALAPACK_LIB_PATH}"
    fi
    echo "ScaLAPACK library: ${SCALAPACK_LIB:-<not found>} (dir: ${SCALAPACK_LIB_DIR})"
    export USE_SCALAPACK=y
    export SCALAPACK="-L${SCALAPACK_LIB_DIR} -lscalapack"
    export SCALAPACK_SIZE=4
fi

# Avoid filesystem check overhead on large clusters
export USE_NOFSCHECK=TRUE

cd "${NWCHEM_TOP}/src"

echo "Configuring NWChem..."
make nwchem_config
test $? -eq 0 || exit $?

echo "Building 64-to-32 integer wrappers..."
make 64_to_32
test $? -eq 0 || exit $?

echo "Building NWChem with ${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES} cores..."
make -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
test $? -eq 0 || exit $?

# Set default memory based on available physical memory
echo "Setting default memory..."
cd "${NWCHEM_TOP}/src"
../contrib/getmem.nwchem || true

echo "NWChem built successfully."
echo "Binary: ${NWCHEM_TOP}/bin/LINUX64/nwchem"
