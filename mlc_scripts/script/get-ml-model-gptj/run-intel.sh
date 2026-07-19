#!/bin/bash

export PATH=${MLC_CONDA_BIN_PATH}:$PATH

export CALIBRATION_DATA_JSON=${MLC_CALIBRATION_DATASET_CNNDM_PATH}


if [[ ${MLC_ML_MODEL_WEIGHT_DATA_TYPES} == "int4" ]]; then
  export INT4_CALIBRATION_DIR=${PWD}/quantized-int4-model
  bash ${MLC_TMP_CURRENT_SCRIPT_PATH}/run-int4-calibration.sh
  cd ${MLC_HARNESS_CODE_ROOT}
  bash run_quantization_int4.sh
else
  cd ${MLC_HARNESS_CODE_ROOT}
  bash run_quantization.sh
fi

test $? -eq 0 || exit $?
