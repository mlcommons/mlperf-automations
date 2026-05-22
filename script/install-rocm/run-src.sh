#!/bin/bash

# Build ROCm LLVM compiler from source

CUR_DIR=$PWD
INSTALL_DIR="${MLC_ROCM_INSTALL_PREFIX}"

echo "Building ROCm LLVM from source..."
echo "  Source: ${MLC_ROCM_LLVM_SRC_PATH}"
echo "  Install prefix: ${INSTALL_DIR}"

mkdir -p build
cd build
test $? -eq 0 || exit $?

echo ""
echo "Running cmake..."
echo "${MLC_ROCM_CMAKE_CMD}"
eval "${MLC_ROCM_CMAKE_CMD}"
test $? -eq 0 || exit $?

echo ""
echo "Building with ninja (this may take a while)..."
ninja
test $? -eq 0 || exit $?

echo ""
echo "Installing..."
ninja install
test $? -eq 0 || exit $?

# Clean build directory (can be very large)
cd "${CUR_DIR}"
rm -rf build

echo ""
echo "ROCm LLVM built and installed to ${INSTALL_DIR}"
