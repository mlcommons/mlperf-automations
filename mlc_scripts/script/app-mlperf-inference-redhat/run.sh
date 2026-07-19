#!/bin/bash
if [[ ${MLC_CALL_MLPERF_RUNNER} == "no" ]]; then
  cd ${MLC_RUN_DIR}
  cmd=${MLC_RUN_CMD}
  echo "${cmd}"
  eval "${cmd}"
  test $? -eq 0 || exit $?
fi
