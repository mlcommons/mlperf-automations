#!/bin/bash

echo "======================================================="

CUR_DIR=${PWD}

# Patch model
cd ${CM_ABTF_SSD_PYTORCH}
if [ ! -f "patchfile-20231129.patch" ] ; then
  echo ""
  echo "Patching ABTF SRC"
  echo ""

  cp ${CM_TMP_CURRENT_SCRIPT_PATH}/patches/coco/patchfile-20231129.patch .
  patch -s -p0 < patchfile-20231129.patch
  test $? -eq 0 || exit $?

  cp ${CM_TMP_CURRENT_SCRIPT_PATH}/patches/coco/patchfile-202400214-export-to-onnx.patch .
  patch -s < patchfile-202400214-export-to-onnx.patch
  test $? -eq 0 || exit $?

fi
cd ${CUR_DIR}

echo ""
${CM_PYTHON_BIN_WITH_PATH} ${CM_ABTF_SSD_PYTORCH}/test_image.py --pretrained-model ${CM_ML_MODEL_FILE_WITH_PATH} --input ${CM_INPUT_IMAGE} --output ${CM_OUTPUT_IMAGE}
test $? -eq 0 || exit $?