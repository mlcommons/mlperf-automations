#!/bin/bash

CUR=${PWD}
INSTALL_DIR=${CUR}/install

echo "******************************************"
echo "${CUR}"
echo "${MLC_CUDNN_TAR_FILE_PATH}"
echo "${MLC_CUDNN_TAR_DIR}"
echo "${MLC_CUDNN_UNTAR_PATH}"
echo "${CUDA_HOME}"
echo "${MLC_CUDA_PATH_INCLUDE}"
echo "${MLC_CUDA_PATH_LIB}"
echo "******************************************"

echo "Untaring file ..."
echo ""
tar -xf ${MLC_CUDNN_TAR_FILE_PATH}
test $? -eq 0 || exit $?

echo "Copying include files ..."
echo ""
${MLC_SUDO} cp -P ${MLC_CUDNN_TAR_DIR}/include/cudnn*.h ${MLC_CUDA_PATH_INCLUDE}
${MLC_SUDO} chmod a+r ${MLC_CUDA_PATH_INCLUDE}/cudnn*.h

echo "Copying lib files ..."
echo ""
${MLC_SUDO} cp -P ${MLC_CUDNN_TAR_DIR}/lib/libcudnn* ${MLC_CUDA_PATH_LIB}
${MLC_SUDO} chmod a+r ${MLC_CUDA_PATH_LIB}/libcudnn*

echo "Adding file that cuDNN is installed ..."
echo ""
if [ "${MLC_SUDO}" == "sudo" ]; then
  ${MLC_SUDO} sh -c "echo '${MLC_VERSION}' > ${CUDA_HOME}/mlc_installed_cudnn.txt"
else
  echo "${MLC_VERSION}" > ${CUDA_HOME}/mlc_installed_cudnn.txt
fi
