#!/bin/bash

set -e

if [[ -z "${MLC_ENZO_SRC_PATH}" ]]; then
    echo "Enzo source not found!"
    exit 1
fi

SRC="${MLC_ENZO_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
./configure

COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
cd src/enzo
make clean >/dev/null 2>&1 || true
make machine-linux-gnu

MACH="Make.mach.linux-gnu"

# Locate the (possibly Debian/Ubuntu-split) serial HDF5 headers and libraries.
HDF5_INC_DIR=""
for d in /usr/include/hdf5/serial /usr/include; do
    [[ -f "$d/hdf5.h" ]] && HDF5_INC_DIR="$d" && break
done
HDF5_LIB_DIR=""
for d in $(find /usr/lib /usr/lib64 -name 'libhdf5.so*' 2>/dev/null | xargs -r -n1 dirname | sort -u); do
    HDF5_LIB_DIR="$d"
    [[ "$d" == *serial* ]] && break
done
echo "HDF5 include: ${HDF5_INC_DIR}   HDF5 lib: ${HDF5_LIB_DIR}"

if [[ -n "${HDF5_INC_DIR}" ]]; then
    sed -i "s|^LOCAL_INCLUDES_HDF5.*|LOCAL_INCLUDES_HDF5 = -I${HDF5_INC_DIR}|" "${MACH}"
fi
if [[ -n "${HDF5_LIB_DIR}" ]]; then
    sed -i "s|^LOCAL_LIBS_HDF5.*|LOCAL_LIBS_HDF5 = -L${HDF5_LIB_DIR} -lhdf5 -lz|" "${MACH}"
fi

# gfortran >= 10 rejects the legacy argument mismatches in Enzo's bundled solvers.
sed -i "s|^MACH_FFLAGS .*|MACH_FFLAGS   = -fno-second-underscore -ffixed-line-length-132 -fallow-argument-mismatch|" "${MACH}"
sed -i "s|^MACH_F90FLAGS .*|MACH_F90FLAGS = -fno-second-underscore -fallow-argument-mismatch|" "${MACH}"

echo "Building Enzo with ${CORES} cores..."
make -j${CORES}

if [[ ! -x enzo.exe ]]; then
    echo "Enzo binary (enzo.exe) not built"
    exit 1
fi
mkdir -p "${SRC}/install-${COMPILER_TAG}/bin" && cp enzo.exe "${SRC}/install-${COMPILER_TAG}/bin/"

echo "Enzo built successfully."
