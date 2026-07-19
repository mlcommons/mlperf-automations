#!/bin/bash
python3() {
  ${MLC_PYTHON_BIN_WITH_PATH} "$@"
}
export -f python3

CUR=${PWD}
mkdir -p install
INSTALL_DIR=${CUR}/install

cd ${MLC_MLPERF_INFERENCE_CLASSIFICATION_AND_DETECTION_PATH}
cd tools
if [[ ${MLC_DATASET_CALIBRATION} == "no" ]]; then
  if [ ! -z ${MLC_DATASET_SIZE} ]; then
    max_images=" -m ${MLC_DATASET_SIZE}"
  else
    max_images=""
  fi
  cmd="./openimages_mlperf.sh -d ${INSTALL_DIR} ${max_images}"
  echo $cmd
  eval $cmd
  test $? -eq 0 || exit 1
else
  if [ -n ${MLC_MLPERF_OPENIMAGES_CALIBRATION_LIST_FILE_WITH_PATH} ]; then
    calibration_file_string=" --calibration-file ${MLC_MLPERF_OPENIMAGES_CALIBRATION_LIST_FILE_WITH_PATH}"
  else
    calibration_file_string=""
  fi
  cmd="./openimages_calibration_mlperf.sh -d \"${INSTALL_DIR}\" ${calibration_file_string}"
  echo $cmd
  eval $cmd
  test $? -eq 0 || exit 1
fi
cd ${INSTALL_DIR}

if [[ ! -d "open-images-v6-mlperf" ]]; then
  ln -sf ../ open-images-v6-mlperf
fi

test $? -eq 0 || exit 1
