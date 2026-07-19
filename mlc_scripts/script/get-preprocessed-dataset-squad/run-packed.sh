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

run "wget --no-check-certificate -nc https://raw.githubusercontent.com/graphcore/examples/v3.2.0/tutorials/blogs_code/packedBERT/spfhp.py"
run "wget --no-check-certificate -nc https://raw.githubusercontent.com/arjunsuresh/ck-qaic/main/package/model-qaic-calibrate-bert/pack.py"
run "${MLC_PYTHON_BIN_WITH_PATH} pack.py ${MLC_DATASET_SQUAD_TOKENIZED_PICKLE_FILE} ./ ${MLC_DATASET_MAX_SEQ_LENGTH}"
