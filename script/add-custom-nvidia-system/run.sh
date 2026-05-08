#!/bin/bash
CUR=$PWD
cd ${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}
if [[ -f scripts/custom_systems/add_custom_system.py ]]; then
  ${MLC_PYTHON_BIN_WITH_PATH} scripts/custom_systems/add_custom_system.py
  test $? -eq 0 || exit $?
else
  echo "add_custom_system.py not found (v6.0+ uses SYSTEM_NAME env var instead), skipping..."
fi
