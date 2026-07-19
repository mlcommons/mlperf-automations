#!/bin/bash

${MLC_PYTHON_BIN_WITH_PATH} ${MLC_TMP_CURRENT_SCRIPT_PATH}/filter.py ${MLC_DATASET_CALIBRATION_ANNOTATIONS_FILE_PATH} > ordered.txt
test $? -eq 0 || exit $?
head -n ${MLC_CALIBRATION_FILTER_SIZE} ordered.txt >filtered.txt
test $? -eq 0 || exit $?
