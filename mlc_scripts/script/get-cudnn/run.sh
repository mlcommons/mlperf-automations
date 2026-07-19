#!/bin/bash
if [ ${MLC_TMP_RUN_COPY_SCRIPT} == "yes" ]; then
    cmd="${MLC_SUDO} cp   ${MLC_TMP_INC_PATH}/*.h   ${MLC_CUDA_PATH_INCLUDE}/"
    echo $cmd
    eval $cmd
    test $? -eq 0 || exit 1

    cmd="${MLC_SUDO} cp -P ${MLC_TMP_LIB_PATH}/libcudnn* ${MLC_CUDA_PATH_LIB}/"
    echo $cmd
    eval $cmd
    test $? -eq 0 || exit 1
fi
