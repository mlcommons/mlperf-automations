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
CUR=$PWD
run "wget --no-check-certificate -nc https://raw.githubusercontent.com/krai/ck-mlperf/master/package/dataset-squad-tokenized_for_bert/tokenize_and_pack.py"

run "${MLC_PYTHON_BIN_WITH_PATH} tokenize_and_pack.py \
    ${MLC_DATASET_SQUAD_VAL_PATH} \
    ${MLC_ML_MODEL_BERT_VOCAB_FILE_WITH_PATH} \
    ${CUR}/bert_tokenized_squad_v1_1 \
    ${MLC_DATASET_MAX_SEQ_LENGTH} \
    ${MLC_DATASET_MAX_QUERY_LENGTH} \
    ${MLC_DATASET_DOC_STRIDE} \
    ${MLC_DATASET_RAW} \
    ${DATASET_CALIBRATION_FILE} \
    ${DATASET_CALIBRATION_ID}"

