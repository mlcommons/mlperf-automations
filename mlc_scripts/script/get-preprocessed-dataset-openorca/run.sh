#!/bin/bash

cd ${MLC_RUN_DIR}
echo "${MLC_RUN_CMD}"
eval "${MLC_RUN_CMD}"
test $? -eq 0 || exit $?

if { [ "${MLC_DATASET_PREPROCESSED_BY_MLC}" = "true" ] || \
     [ "${MLC_DATASET_PREPROCESSED_BY_MLC}" = "yes" ] || \
     [ "${MLC_DATASET_PREPROCESSED_BY_MLC}" = "1" ]; } && \
   [ "${MLC_TMP_DATASET_PREPROCESS_STEP_PROVIDER}" = "nvidia" ]; then

    ${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/nvidia_preprocess.py \
        -d ${MLC_OPENORCA_PREPROCESSED_ROOT} \
        -o ${MLC_OPENORCA_PREPROCESSED_ROOT}/preprocessed_data
    test $? -eq 0 || exit $?
fi

