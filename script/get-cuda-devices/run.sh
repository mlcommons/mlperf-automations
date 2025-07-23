#!/bin/bash

# Compile

rm a.out

echo ""
echo "NVCC path: ${MLC_NVCC_BIN_WITH_PATH}"
echo ""

echo ""
echo "Checking compiler version ..."
echo ""

${MLC_NVCC_BIN_WITH_PATH} -V

echo ""
echo "Compiling program ..."
echo ""

cd ${MLC_TMP_CURRENT_SCRIPT_PATH}

${MLC_NVCC_BIN_WITH_PATH} -allow-unsupported-compiler print_cuda_devices.cu
test $? -eq 0 || exit 1

# Return to the original path obtained in MLC

echo ""
echo "Running program ..."
echo ""

cd ${MLC_TMP_CURRENT_PATH}

${MLC_TMP_CURRENT_SCRIPT_PATH}/a.out > tmp-run.out
test $? -eq 0 || exit 1
