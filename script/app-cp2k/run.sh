#!/bin/bash

set -e
CUR=$PWD
INSTALL_DIR=$CUR/install
mkdir -p ${INSTALL_DIR}

TOOLCHAIN_DIR="$(realpath "${MLC_CP2K_SRC_PATH}/tools/toolchain")"
cd "${TOOLCHAIN_DIR}"

# Set flags for the toolchain installer to find our custom OpenBLAS
export CPPFLAGS="-I${MLC_BLAS_INC}"
export LDFLAGS="-L$(dirname ${MLC_BLAS_LIB})"

# Install the toolchain
./install_cp2k_toolchain.sh --with-openblas=system

# Source the setup script to configure the environment for the CP2K build
source "${TOOLCHAIN_DIR}/install/setup"

# Now, build CP2K itself
cd "$(realpath "${MLC_CP2K_SRC_PATH}")"
mkdir -p build
cd build

# Configure the build with CMake
# The toolchain setup should provide all necessary paths
cmake .. -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR} \
         -DCP2K_USE_FFTW3=ON \
         -DCP2K_USE_LIBINT2=ON \
         -DCP2K_USE_LIBXC=ON \
         -DCP2K_USE_LIBXSMM=ON \
         -DCP2K_USE_SPGLIB=ON \
         -DCP2K_USE_VORI=ON

# Compile and install
make install -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
