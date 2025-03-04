#!/bin/bash
python3() {
  ${MLC_PYTHON_BIN_WITH_PATH} "$@"
}
export -f python3

CUR=${PWD}
INSTALL_DIR=${CUR}

cd ${MLC_RUN_DIR}

if [[ ${MLC_DATASET_CALIBRATION} == "no" ]]; then
  if [ ! -z ${MLC_DATASET_SIZE} ]; then
    max_images=" -m ${MLC_DATASET_SIZE}"
  else
    max_images=""
  fi

  # deleting existing incomplete downloads if any
  if [ -f "${INSTALL_DIR}/download_aux/annotations_trainval2014.zip" ]; then
    echo "File annotations_trainval2014.zip already exists. Deleting it."
    rm ${INSTALL_DIR}/download_aux/annotations_trainval2014.zip
  fi
  
  cmd="./download-coco-2014.sh -d ${INSTALL_DIR}  ${max_images}"
  echo $cmd
  eval $cmd
  test $? -eq 0 || exit $?
else
  cmd="./download-coco-2014-calibration.sh -d ${INSTALL_DIR} -n ${MLC_DATASET_COCO2014_NUM_WORKERS}"
  echo $cmd
  eval $cmd
  test $? -eq 0 || exit $?
fi
if [[ ${MLC_GENERATE_SAMPLE_ID} == "yes" ]]; then
  cmd="python3 sample_ids.py --tsv-path ${INSTALL_DIR}/captions/captions.tsv --output-path ${INSTALL_DIR}/sample_ids.txt"
  echo $cmd
  eval $cmd
  test $? -eq 0 || exit $?
fi
cd ${INSTALL_DIR}

test $? -eq 0 || exit $?
