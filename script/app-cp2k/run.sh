#!/bin/bash

set -e

if [[ -z "${MLC_CP2K_SRC_PATH}" ]]; then
    echo "CP2K source not found!"
    exit 1
fi

CUR=$PWD
INSTALL_DIR=$CUR/install

CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

# Clean build if requested
if [[ "${MLC_CP2K_CLEAN_BUILD}" == "true" ]]; then
    echo "Clean build requested. Removing build and toolchain install dirs..."
    rm -rf "${INSTALL_DIR}"
    rm -rf "$(realpath "${MLC_CP2K_SRC_PATH}")/build"
    rm -rf "$(realpath "${MLC_CP2K_SRC_PATH}/tools/toolchain")/build"
    rm -rf "$(realpath "${MLC_CP2K_SRC_PATH}/tools/toolchain")/install"
fi

mkdir -p ${INSTALL_DIR}

echo "Building CP2K with compiler: ${MLC_CP2K_COMPILER:-gcc}"
echo "  CC:  ${MLC_CP2K_CC}"
echo "  CXX: ${MLC_CP2K_CXX}"
echo "  FC:  ${MLC_CP2K_FC}"

# Set compiler environment variables for cmake and toolchain
export CC="${MLC_CP2K_CC}"
export CXX="${MLC_CP2K_CXX}"
export FC="${MLC_CP2K_FC}"

# Prepend compiler bin dir to PATH so the toolchain finds the correct clang/clang++/flang
COMPILER_BIN_DIR="$(dirname "${MLC_CP2K_CC}")"
export PATH="${COMPILER_BIN_DIR}:${PATH}"

TOOLCHAIN_DIR="$(realpath "${MLC_CP2K_SRC_PATH}/tools/toolchain")"
cd "${TOOLCHAIN_DIR}"

# Set flags for the toolchain installer to find our custom OpenBLAS
export CPPFLAGS="-I${MLC_BLAS_INC}"
export LDFLAGS="-L$(dirname ${MLC_BLAS_LIB})"

# Build toolchain arguments
TOOLCHAIN_ARGS="--with-openblas=system"

# Add compiler-specific toolchain args
if [[ "${MLC_CP2K_COMPILER}" == "aocc" || "${MLC_CP2K_COMPILER}" == "llvm" ]]; then
    TOOLCHAIN_ARGS="${TOOLCHAIN_ARGS} --with-amd"
    # System OpenMPI Fortran modules are incompatible with AOCC flang;
    # build MPICH from source so MPI Fortran works correctly.
    TOOLCHAIN_ARGS="${TOOLCHAIN_ARGS} --with-openmpi=no --with-mpich=install"
    # ELPA: classic flang doesn't support -msse4 flag used by ELPA configure
    # COSMA: cmake_policy compatibility issue with newer cmake
    # SIRIUS: AOCC clang++ ICE on density/density.cpp (compiler bug)
    TOOLCHAIN_ARGS="${TOOLCHAIN_ARGS} --with-elpa=no --with-cosma=no --with-sirius=no"
    # DBCSR: classic flang can't build mpi_f08.mod; disable USE_MPI_F08
    # DBCSR: libxsmm .mod files from gfortran are incompatible with classic flang; use blas SMM
    sed -i 's/-DUSE_MPI=ON -DUSE_MPI_F08=ON/-DUSE_MPI=ON -DUSE_MPI_F08=OFF/' \
        "${TOOLCHAIN_DIR}/scripts/stage9/install_dbcsr.sh"
    sed -i 's/-DUSE_SMM=libxsmm/-DUSE_SMM=blas/' \
        "${TOOLCHAIN_DIR}/scripts/stage9/install_dbcsr.sh"
elif [[ "${MLC_CP2K_COMPILER}" == "oneapi" ]]; then
    TOOLCHAIN_ARGS="${TOOLCHAIN_ARGS} --with-intel"
fi

# For AOCC/LLVM: set MPI_HOME so cmake FindMPI finds MPICH (built by toolchain)
# instead of system OpenMPI whose Fortran modules are incompatible with flang
if [[ "${MLC_CP2K_COMPILER}" == "aocc" || "${MLC_CP2K_COMPILER}" == "llvm" ]]; then
    MPICH_DIR="${TOOLCHAIN_DIR}/install/mpich-5.0.1"
    export MPI_HOME="${MPICH_DIR}"
    export PATH="${MPICH_DIR}/bin:${PATH}"
    echo "MPI_HOME set to: ${MPI_HOME}"
fi

echo "Running CP2K toolchain installer..."
echo "  Args: ${TOOLCHAIN_ARGS}"
./install_cp2k_toolchain.sh ${TOOLCHAIN_ARGS}

# For AOCC/LLVM: classic flang needs DBCSR internal .mod files (transitive module deps)
if [[ "${MLC_CP2K_COMPILER}" == "aocc" || "${MLC_CP2K_COMPILER}" == "llvm" ]]; then
    DBCSR_BUILD_DIR="${TOOLCHAIN_DIR}/build/dbcsr-2.9.1/build-cpu/src"
    DBCSR_INSTALL_INC="${TOOLCHAIN_DIR}/install/dbcsr-2.9.1/include"
    if [ -d "${DBCSR_BUILD_DIR}" ] && [ -d "${DBCSR_INSTALL_INC}" ]; then
        echo "Copying DBCSR internal .mod files for classic flang compatibility..."
        cp -n "${DBCSR_BUILD_DIR}"/*.mod "${DBCSR_INSTALL_INC}/" 2>/dev/null || true
    fi
fi

# Source the setup script to configure the environment for the CP2K build
source "${TOOLCHAIN_DIR}/install/setup"

# Re-export our compiler settings (the toolchain setup script overrides CC/CXX/FC)
export CC="${MLC_CP2K_CC}"
export CXX="${MLC_CP2K_CXX}"
export FC="${MLC_CP2K_FC}"
echo "Compiler after toolchain setup (re-exported):"
echo "  CC:  ${CC}"
echo "  CXX: ${CXX}"
echo "  FC:  ${FC}"

# Build CP2K with CMake
cd "$(realpath "${MLC_CP2K_SRC_PATH}")"
mkdir -p build
cd build

# Build cmake options based on compiler
CMAKE_EXTRA_OPTS=""
if [[ "${MLC_CP2K_COMPILER}" == "aocc" || "${MLC_CP2K_COMPILER}" == "llvm" ]]; then
    CMAKE_EXTRA_OPTS="-DCP2K_USE_ELPA=OFF -DCP2K_USE_COSMA=OFF -DCP2K_USE_SIRIUS=OFF"
    # Classic flang needs explicit free-form flag; CP2K cmake doesn't recognize it
    CMAKE_EXTRA_OPTS="${CMAKE_EXTRA_OPTS} -DCMAKE_Fortran_FLAGS=-ffree-form"
fi

# Set MPI cmake options
MPI_CMAKE_OPTS=""
if [[ "" == "aocc" || "" == "llvm" ]]; then
    MPI_CMAKE_OPTS="-DMPI_HOME=${MPICH_DIR} -DCMAKE_PREFIX_PATH=${MPICH_DIR}"
fi

echo "Configuring CP2K with CMake..."
cmake .. \
    -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR} \
    -DCMAKE_C_COMPILER=${MLC_CP2K_CC} \
    -DCMAKE_CXX_COMPILER=${MLC_CP2K_CXX} \
    -DCMAKE_Fortran_COMPILER=${MLC_CP2K_FC} \
    -DCP2K_USE_FFTW3=ON \
    -DCP2K_USE_LIBINT2=ON \
    -DCP2K_USE_LIBXC=ON \
    -DCP2K_USE_LIBXSMM=ON \
    -DCP2K_USE_MPI=ON \
    ${MPI_CMAKE_OPTS} \
    ${CMAKE_EXTRA_OPTS}

echo "Building CP2K with ${CORES} cores..."
cmake --build . -j${CORES}

echo "Installing CP2K..."
cmake --install .

echo "CP2K built successfully with ${MLC_CP2K_COMPILER:-gcc} compiler."
