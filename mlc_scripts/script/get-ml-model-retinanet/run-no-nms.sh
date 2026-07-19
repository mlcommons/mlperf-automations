#!/bin/bash

#MLC Script location: ${MLC_TMP_CURRENT_SCRIPT_PATH}

#To export any variable
#echo "VARIABLE_NAME=VARIABLE_VALUE" >>tmp-run-env.out

#${MLC_PYTHON_BIN_WITH_PATH} contains the path to python binary if "get,python" is added as a dependency



function exit_if_error() {
  test $? -eq 0 || exit $?
}

function run() {
  echo "Running: "
  echo "$1"
  echo ""
  if [[ ${MLC_FAKE_RUN} != 'yes' ]]; then
    eval "$1"
    exit_if_error
  fi
}

#Add your run commands here...
# run "$MLC_RUN_CMD"

cmd="PYTHONPATH=${PYTHONPATH}:${MLC_MLPERF_TRAINING_REPO_PATCHED_PATH}/single_stage_detector/ssd/ ${MLC_PYTHON_BIN_WITH_PATH} ${MLC_MLPERF_TRAINING_REPO_PATCHED_PATH}/single_stage_detector/scripts/pth_to_onnx.py --input ${MLC_ML_MODEL_RETINANET_PYTORCH_WEIGHTS_FILE_PATH} --output $PWD/retinanet.onnx --image-size 800 800"
run "$cmd"

if [[ ${MLC_QAIC_PRINT_NODE_PRECISION_INFO} == "yes" ]]; then
  cmd="${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/node-precision-info.py --input $PWD/retinanet.onnx --output $PWD/node-precision-info.yaml"
  run "$cmd"
fi
