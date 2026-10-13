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

${MLC_NVCC_BIN_WITH_PATH} -allow-unsupported-compiler ${MLC_TMP_CURRENT_SCRIPT_PATH}/print_cuda_devices.cu
test $? -eq 0 || exit $?

# Return to the original path obtained in MLC

echo ""
echo "Running program ..."
echo ""

./a.out > tmp-run.out
test $? -eq 0 || exit $?

# Host interconnect (PCIe gen/width) and GPU topology for postprocess.
# Optional: without nvidia-smi the files are absent and those fields stay
# unset.
if command -v nvidia-smi > /dev/null 2>&1; then
  nvidia-smi -q > tmp-nvidia-smi-q.out 2> /dev/null || true
  nvidia-smi topo -m > tmp-nvidia-smi-topo.out 2> /dev/null || true
fi
