#/bin/bash
if [[ ${CM_TMP_MODEL_ADDITIONAL_NAME} ]]; then
  ln -s ${CM_ML_MODEL_FILE} ${CM_TMP_MODEL_ADDITIONAL_NAME}
fi