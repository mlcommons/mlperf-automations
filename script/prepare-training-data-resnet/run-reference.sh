#!/bin/bash

#CM Script location: ${MLC_TMP_CURRENT_SCRIPT_PATH}

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
DATA_DIR=${MLC_DATA_DIR:-"$PWD/data"}

cd ${MLC_RUN_DIR}
mkdir -p ${DATA_DIR}/tfrecords
cmd="python3 ${MLC_IMAGENET_TO_GCS_SCRIPT_PATH} \
  --raw_data_dir=${MLC_DATASET_IMAGENET_TRAIN_PATH} \
  --local_scratch_dir=${DATA_DIR}/tfrecords \
  --nogcs_upload"
run "$cmd"
