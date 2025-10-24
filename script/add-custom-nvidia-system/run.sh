#!/bin/bash
if [ "${MLC_CUSTOM_CONFIG}" != "yes" ]; then
    CUR=$PWD
    cd "${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}"
    "${MLC_PYTHON_BIN_WITH_PATH}" scripts/custom_systems/add_custom_system.py
    test $? -eq 0 || exit $?
    cd "$CUR"
else
    mkdir -p "${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/configs/${MLC_NVIDIA_SYSTEM_NAME}"
    cp "${MLC_TMP_CURRENT_SCRIPT_PATH}/dummy_config.py" "${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/configs/${MLC_NVIDIA_SYSTEM_NAME}/"
fi
