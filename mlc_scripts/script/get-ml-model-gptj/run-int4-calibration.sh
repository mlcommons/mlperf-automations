#!/bin/bash

export PATH=${MLC_CONDA_BIN_PATH}:$PATH

echo ${MLC_CALIBRATION_CODE_ROOT}
cd ${MLC_CALIBRATION_CODE_ROOT}/gpt-j/pytorch-cpu/INT4
pip install -r requirements.txt
bash run_calibration_int4.sh

test $? -eq 0 || exit $?
