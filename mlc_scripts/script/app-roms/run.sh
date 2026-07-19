#!/bin/bash

set -e

if [[ -z "${MLC_ROMS_SRC_PATH}" ]]; then
    echo "ROMS source not found!"
    exit 1
fi

ROMS_SRC="${MLC_ROMS_SRC_PATH}"
BUILD_DIR="${ROMS_SRC}/build"
INSTALL_DIR="${ROMS_SRC}/install"

ROMS_APP="${MLC_ROMS_APPLICATION:-BENCHMARK}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

echo "Building ROMS application: ${ROMS_APP}"
echo "Source: ${ROMS_SRC}"
echo "Build directory: ${BUILD_DIR}"

mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# Header files are in ROMS/Include
MY_HEADER_DIR="${ROMS_SRC}/ROMS/Include"

# Set NetCDF for ROMS cmake detection.
# ROMS cmake uses regex "-l[^ \t]*" to parse NETCDF_LIBS which incorrectly
# matches "-linux-gnu" in paths like /usr/lib/x86_64-linux-gnu.
# Only use -l flags (no -L) since libs are in system default paths.
export NETCDF_LIBS="-lnetcdff -lnetcdf"
export NETCDF_INCDIR="/usr/include"

# Configure with cmake
# ROMS cmake uses ROMS_APP (not ROMS_APPLICATION)
cmake "${ROMS_SRC}" \
    -DROMS_APP="${ROMS_APP}" \
    -DMY_HEADER_DIR="${MY_HEADER_DIR}" \
    -DCMAKE_Fortran_COMPILER=mpif90 \
    -DMPI=ON \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
    -DCMAKE_BUILD_TYPE=Release

echo "Building ROMS with ${CORES} cores..."
cmake --build . -j${CORES}

echo "Installing ROMS..."
cmake --install . || true

echo "ROMS built successfully."
