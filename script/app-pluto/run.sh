#!/bin/bash

set -e

if [[ -z "${MLC_PLUTO_SRC_PATH}" ]]; then
    echo "PLUTO source not found!"
    exit 1
fi

SRC="${MLC_PLUTO_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
export PLUTO_DIR="${SRC}"

# PLUTO is configured per test problem via an interactive setup.py that links
# the physics-module headers (mod_defs.h, ...) selected in definitions.h.
# Here we set up the Sod shock-tube problem non-interactively as a best effort.
cd "${SRC}/Test_Problems/HD/Sod"
cp definitions_01.h definitions.h
cp "${PLUTO_DIR}/Src/Templates/makefile" .
sed -i "s|^ARCH         =.*|ARCH         = Linux.gcc.defs|" makefile
sed -i "s|^PLUTO_DIR    =.*|PLUTO_DIR    = ${PLUTO_DIR}|" makefile
make -j"${CORES}"

echo "PLUTO build step completed."
