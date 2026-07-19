#!/bin/bash

if [[ ${MLC_RUN_DOCKER_CONTAINER} == "yes" ]]; then
  exit 0
fi

#echo ${MLC_PYTHON_BIN}
#echo ${MLC_DATASET_PATH}
#echo ${MLC_DATASET_AUX_PATH}
#echo ${MLC_ML_MODEL_FILE_WITH_PATH}
MLC_PYTHON_BIN=${MLC_PYTHON_BIN_WITH_PATH:-python3}
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

# connect MLC intelligent components with CK env
export CK_ENV_ONNX_MODEL_ONNX_FILEPATH=${MLC_ML_MODEL_FILE_WITH_PATH}
export CK_ENV_ONNX_MODEL_INPUT_LAYER_NAME="input_tensor:0"
export CK_ENV_ONNX_MODEL_OUTPUT_LAYER_NAME="softmax_tensor:0"
export CK_ENV_DATASET_IMAGENET_VAL=${MLC_DATASET_PATH}
export CK_CAFFE_IMAGENET_SYNSET_WORDS_TXT=${MLC_DATASET_AUX_PATH}/synset_words.txt
export ML_MODEL_DATA_LAYOUT="NCHW"
export CK_BATCH_SIZE=${MLC_BATCH_SIZE}
export CK_BATCH_COUNT=${MLC_BATCH_COUNT}

if [[ "${MLC_INPUT}" != "" ]]; then export MLC_IMAGE=${MLC_INPUT}; fi

PIP_EXTRA=`${MLC_PYTHON_BIN} -c "import importlib.metadata; print(' --break-system-packages ' if int(importlib.metadata.version('pip').split('.')[0]) >= 23 else '')"`

echo ""
${MLC_PYTHON_BIN} -m pip install -r ${MLC_TMP_CURRENT_SCRIPT_PATH}/requirements.txt ${PIP_EXTRA}
test $? -eq 0 || exit 1

echo ""
${MLC_PYTHON_BIN} ${MLC_TMP_CURRENT_SCRIPT_PATH}/src/onnx_classify.py
test $? -eq 0 || exit 1

# Just a demo to pass environment variables from native scripts back to MLC workflows
echo "MLC_APP_IMAGE_CLASSIFICATION_ONNX_PY=sucess" > tmp-run-env.out
