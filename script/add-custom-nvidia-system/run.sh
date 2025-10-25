#!/bin/bash
if [ "${MLC_CUSTOM_CONFIG}" != "yes" ]; then
    CUR=$PWD
    cd "${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}"
    "${MLC_PYTHON_BIN_WITH_PATH}" scripts/custom_systems/add_custom_system.py
    test $? -eq 0 || exit $?
    cd "$CUR"
fi
