#!/bin/bash
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
MLC_RUN_CMD="${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/send-email.py"
run "$MLC_RUN_CMD"
