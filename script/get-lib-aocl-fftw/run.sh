#!/bin/bash
set -e

SRC="${MLC_AOCL_FFTW_SRC_PATH}"
PREFIX="${MLC_AOCL_FFTW_INSTALL_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
if [[ -z "${SRC}" || ! -d "${SRC}" ]]; then
    echo "AOCL-FFTW source not found!"
    exit 1
fi

# Dynamic dispatcher: one portable library across Zen generations.
COMMON_FLAGS="--prefix=${PREFIX} --enable-shared --enable-threads --enable-openmp \
  --enable-sse2 --enable-avx --enable-avx2 --enable-avx512 \
  --enable-amd-opt --enable-dynamic-dispatcher"
if command -v mpicc >/dev/null 2>&1; then
    COMMON_FLAGS="${COMMON_FLAGS} --enable-mpi --enable-amd-mpifft"
fi

# Build double and single precision out of tree so both land in one prefix.
for prec in double float; do
    BUILD="${SRC}/build-${prec}"
    rm -rf "${BUILD}" && mkdir -p "${BUILD}" && cd "${BUILD}"
    PREC_FLAG=""
    [[ "${prec}" == "float" ]] && PREC_FLAG="--enable-float"
    "${SRC}/configure" ${COMMON_FLAGS} ${PREC_FLAG} ${MLC_AOCL_FFTW_EXTRA_CONFIGURE_FLAGS}
    # MAKEINFO=true: skip the texinfo docs (makeinfo is usually not installed).
    make -j"${CORES}" MAKEINFO=true
    make install MAKEINFO=true
done

echo "AOCL-FFTW installed to ${PREFIX}"
