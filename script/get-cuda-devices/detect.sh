#!/bin/bash

${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/detect.py
test $? -eq 0 || exit 11

# Host interconnect (PCIe gen/width) and GPU topology for postprocess.
# Optional: without nvidia-smi the files are absent and those fields stay
# unset.
if command -v nvidia-smi > /dev/null 2>&1; then
  nvidia-smi -q > tmp-nvidia-smi-q.out 2> /dev/null || true
  nvidia-smi topo -m > tmp-nvidia-smi-topo.out 2> /dev/null || true
fi
