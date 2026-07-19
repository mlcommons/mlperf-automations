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

CUR=${MLC_DATA_DIR:-"$PWD/data"}
cd ${MLC_RUN_DIR}

if [[ ${MLC_TMP_VARIATION} == "nvidia" ]]; then
  bash ${MLC_TMP_CURRENT_SCRIPT_PATH}/run-nvidia.sh
elif [[ ${MLC_TMP_VARIATION} == "reference" ]]; then
  bash ${MLC_TMP_CURRENT_SCRIPT_PATH}/run-reference.sh
fi
