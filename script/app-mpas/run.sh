#!/bin/bash

set -e

if [[ -z "${MLC_MPAS_SRC_PATH}" ]]; then
    echo "MPAS source not found!"
    exit 1
fi

SRC="${MLC_MPAS_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"

# MPAS v8 bundles SMIOL, so it can build against system NetCDF without external
# PIO/PnetCDF. Point NETCDF at the system prefix and use the gfortran target.
export NETCDF=/usr
export NETCDFF=/usr
export PNETCDF=/usr
export USE_PIO2=false
export PRECISION=single

make gfortran CORE=init_atmosphere

echo "MPAS build step completed."
