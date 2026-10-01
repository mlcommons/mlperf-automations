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
cd "${SRC}/ks_imp_dyn"
cp -f ../Makefile .

echo "Building MILC su3_rmd (serial, GNU compiler)..."
make su3_rmd COMPILER=gnu MPP=false

if [[ ! -x su3_rmd ]]; then
    echo "MILC binary (su3_rmd) not built"
    exit 1
fi

echo "MILC su3_rmd built successfully."
