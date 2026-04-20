#!/bin/bash

set -e

if [[ -z "${MLC_WRF_SRC_PATH}" ]]; then
    echo "WRF source not found!"
    exit 1
fi

WRF_SRC="${MLC_WRF_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

# Set up NetCDF environment
export NETCDF=$(nc-config --prefix 2>/dev/null || nf-config --prefix 2>/dev/null || echo "/usr")
export NETCDF_classic=1

# Find HDF5 OpenMPI library path
# On Ubuntu, libhdf5-openmpi-dev installs to /usr/lib/x86_64-linux-gnu/hdf5/openmpi/
HDF5_LIB_DIR=""
for d in /usr/lib/x86_64-linux-gnu/hdf5/openmpi /usr/lib/hdf5/openmpi /usr/lib64/hdf5/openmpi; do
    if [[ -f "${d}/libhdf5.so" ]]; then
        HDF5_LIB_DIR="${d}"
        break
    fi
done

# If OpenMPI variant not found, try serial
if [[ -z "${HDF5_LIB_DIR}" ]]; then
    for d in /usr/lib/x86_64-linux-gnu/hdf5/serial /usr/lib/hdf5/serial /usr/lib64; do
        if [[ -f "${d}/libhdf5.so" ]]; then
            HDF5_LIB_DIR="${d}"
            break
        fi
    done
fi

# Set HDF5 to the prefix (parent of lib dir)
if [[ -n "${HDF5_LIB_DIR}" ]]; then
    export HDF5=$(dirname "${HDF5_LIB_DIR}")
    # Also add to LIBRARY_PATH and LD_LIBRARY_PATH so linker can find them
    export LIBRARY_PATH="${HDF5_LIB_DIR}:${LIBRARY_PATH:-}"
    export LD_LIBRARY_PATH="${HDF5_LIB_DIR}:${LD_LIBRARY_PATH:-}"
    # Set LDFLAGS for WRF configure
    export LDFLAGS="-L${HDF5_LIB_DIR} ${LDFLAGS:-}"
else
    export HDF5="/usr"
fi

# WRF requires both C and Fortran NetCDF
export NETCDF_C=$(nc-config --prefix 2>/dev/null || echo "/usr")
export NETCDF_FORTRAN=$(nf-config --prefix 2>/dev/null || echo "/usr")

echo "NETCDF: ${NETCDF}"
echo "HDF5: ${HDF5}"
echo "HDF5_LIB_DIR: ${HDF5_LIB_DIR}"

cd "${WRF_SRC}"

# Clean any previous builds
if [[ -f configure.wrf ]]; then
    ./clean -a 2>/dev/null || true
fi

# Configure WRF
# Option 34 = GNU (gfortran/gcc) dm+sm on Linux x86_64
# Nesting option from env (default 1 = basic)
echo "Configuring WRF..."
echo -e "34\n${MLC_WRF_NESTING:-1}" | ./configure 2>&1

# Verify configure succeeded
if [[ ! -f configure.wrf ]]; then
    echo "WRF configure failed!"
    exit 1
fi

# Patch configure.wrf to add HDF5 library path if needed
if [[ -n "${HDF5_LIB_DIR}" ]]; then
    if ! grep -q "${HDF5_LIB_DIR}" configure.wrf; then
        sed -i "s|-lhdf5_hl_fortran|-L${HDF5_LIB_DIR} -lhdf5_hl_fortran|g" configure.wrf
        echo "Patched configure.wrf with HDF5 library path"
    fi
fi

# Fix HDF5 library names for Ubuntu (libhdf5hl_fortran vs libhdf5_hl_fortran)
if [[ -n "${HDF5_LIB_DIR}" ]]; then
    # Check if Ubuntu-style naming is used (libhdf5hl_fortran instead of libhdf5_hl_fortran)
    if [[ -f "${HDF5_LIB_DIR}/libhdf5hl_fortran.so" ]] && [[ ! -f "${HDF5_LIB_DIR}/libhdf5_hl_fortran.so" ]]; then
        sed -i "s|-lhdf5_hl_fortran|-lhdf5hl_fortran|g" configure.wrf
        echo "Patched configure.wrf: hdf5_hl_fortran -> hdf5hl_fortran (Ubuntu naming)"
    fi
fi

# Add NetCDF Fortran libraries if missing from LIB_EXTERNAL
# WRF configure sometimes fails to add -lnetcdff -lnetcdf after -lwrfio_nf
if ! grep -q "\-lnetcdff" configure.wrf; then
    NETCDF_FLIBS=$(nf-config --flibs 2>/dev/null || echo "-lnetcdff -lnetcdf")
    # Extract just the -l flags and -L flags we need
    NETCDF_LDIR=$(nf-config --prefix 2>/dev/null)/lib
    if [[ -d "${NETCDF_LDIR}" ]]; then
        sed -i "s|-lwrfio_nf|-lwrfio_nf -L${NETCDF_LDIR} -lnetcdff -lnetcdf|g" configure.wrf
    else
        sed -i "s|-lwrfio_nf|-lwrfio_nf -lnetcdff -lnetcdf|g" configure.wrf
    fi
    echo "Patched configure.wrf: added -lnetcdff -lnetcdf to link line"
fi

# Build WRF
BUILD_TYPE="${MLC_WRF_BUILD_TYPE:-em_real}"
echo "Building WRF (${BUILD_TYPE}) with ${CORES} cores..."
./compile -j ${CORES} ${BUILD_TYPE} 2>&1

# Check if wrf.exe was actually created
if [[ ! -f main/wrf.exe ]]; then
    echo "WRF compile failed - wrf.exe not found!"
    exit 1
fi

echo "WRF built successfully."
echo "Binary: ${WRF_SRC}/main/wrf.exe"
