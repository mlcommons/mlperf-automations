#!/bin/bash

set -e

if [[ -z "${MLC_VASP_SRC_PATH}" ]]; then
    echo "VASP source path not set! VASP requires a license purchase from https://vasp.at"
    echo "Set MLC_VASP_SRC_PATH to point to your VASP source directory."
    exit 1
fi

SRC="${MLC_VASP_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

if [[ ! -d "${SRC}" ]]; then
    echo "VASP source directory not found at ${SRC}"
    exit 1
fi

echo "Building VASP..."
echo "Source: ${SRC}"

cd "${SRC}"

# VASP uses make with arch-specific makefile.include
if [[ ! -f makefile.include ]]; then
    # Try to use the GNU + OpenMPI template
    if [[ -f arch/makefile.include.gnu_omp ]]; then
        cp arch/makefile.include.gnu_omp makefile.include
    elif [[ -f arch/makefile.include.linux_gnu ]]; then
        cp arch/makefile.include.linux_gnu makefile.include
    else
        echo "No suitable makefile.include template found in arch/"
        echo "Please provide a makefile.include in the VASP source directory."
        exit 1
    fi
fi

make DEPS=1 -j${CORES} all

echo "VASP built successfully."
