#!/bin/bash

MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

#if [[ ${MLC_HOST_PLATFORM_FLAVOR} == "arm64" ]]; then
#    ${MLC_PYTHON_BIN} -m pip install -i https://test.pypi.org/simple/ onnxruntime==1.9.0.dev174552
#fi

export USE_TVM=yes


wget -nc https://raw.githubusercontent.com/mlcommons/ck-mlops/main/program/ml-task-image-classification-tvm-onnx-cpu/synset.txt
test $? -eq 0 || exit 1

${MLC_PYTHON_BIN} -m pip install -r ${MLC_TMP_CURRENT_SCRIPT_PATH}/requirements.txt
test $? -eq 0 || exit 1

if [[ "${MLC_INPUT}" != "" ]]; then 
  export MLC_IMAGE=${MLC_INPUT}
else
  export MLC_IMAGE=${MLC_DATASET_PATH}/ILSVRC2012_val_00000001.JPEG
fi


${MLC_PYTHON_BIN} ${MLC_TMP_CURRENT_SCRIPT_PATH}/src/classify.py --image ${MLC_IMAGE}
test $? -eq 0 || exit 1
