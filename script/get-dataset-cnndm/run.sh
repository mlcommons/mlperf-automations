#!/bin/bash

if [[ "${MLC_TMP_ML_MODEL}" != "llama3_1-8b" ]]; then
  CUR=${PWD}
  mkdir -p install
  export DATASET_CNNDM_PATH=${CUR}/install

  cd ${MLC_MLPERF_INFERENCE_SOURCE}
  cd language/gpt-j

  if [[ ${MLC_DATASET_CALIBRATION} == "no" ]]; then
    cmd="${MLC_PYTHON_BIN_WITH_PATH} download_cnndm.py"
    echo $cmd
    eval $cmd
    test $? -eq 0 || exit 1
  else
    cmd="${MLC_PYTHON_BIN_WITH_PATH} prepare-calibration.py --calibration-list-file calibration-list.txt --output-dir ${DATASET_CNNDM_PATH}"
    echo $cmd
    eval $cmd
    test $? -eq 0 || exit 1
  fi
  test $? -eq 0 || exit 1
fi