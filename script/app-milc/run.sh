#!/bin/bash

set -e

if [[ -z "${MLC_MILC_SRC_PATH}" ]]; then
    echo "MILC source not found!"
    exit 1
fi

SRC="${MLC_MILC_SRC_PATH}"

# Build the Kogut-Susskind improved dynamical (asqtad) application su3_rmd.
# MILC's application build expects the master Makefile copied into the
# application directory; the recursive rule then invokes `make -f Makefile`.
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
case "${COMPILER_TAG}" in oneapi) MLCMP=intel ;; *) MLCMP=gnu ;; esac
cd "${SRC}/ks_imp_dyn"
cp -f ../Makefile .
make clean >/dev/null 2>&1 || true
rm -f su3_rmd *.o
echo "Building MILC su3_rmd (serial, ${COMPILER_TAG})..."
make su3_rmd COMPILER=${MLCMP} MPP=false ${CC:+CC="${CC}"}

if [[ ! -x su3_rmd ]]; then
    echo "MILC binary (su3_rmd) not built"
    exit 1
fi
mkdir -p "${SRC}/install-${COMPILER_TAG}/bin" && cp su3_rmd "${SRC}/install-${COMPILER_TAG}/bin/"

echo "MILC su3_rmd built successfully."
