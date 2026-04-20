#!/bin/bash

INSTALL_DIR=${MLC_CUDA_INSTALL_PREFIX}/install
${MLC_SUDO} mkdir -p "${MLC_CUDA_INSTALL_PREFIX}" || exit $?

cmd="${MLC_SUDO} bash \"${MLC_CUDA_RUN_FILE_PATH}\" --toolkitpath=\"${INSTALL_DIR}\" --defaultroot=\"${INSTALL_DIR}\" --toolkit ${CUDA_ADDITIONAL_INSTALL_OPTIONS} --silent --override ${MLC_CUDA_EXTRA_INSTALL_ARGS}"
echo "${cmd}"
eval "${cmd}"
test $? -eq 0 || exit $?
