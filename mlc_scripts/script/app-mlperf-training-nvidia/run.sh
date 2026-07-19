#!/bin/bash

cmd="cd ${MLC_RUN_DIR}"
echo "$cmd"
eval "$cmd"

if [[ ${MLC_MLPERF_MODEL} == "bert" ]]; then
  bash ${MLC_TMP_CURRENT_SCRIPT_PATH}/run-bert-training.sh
  test $? -eq 0 || exit $?
fi
