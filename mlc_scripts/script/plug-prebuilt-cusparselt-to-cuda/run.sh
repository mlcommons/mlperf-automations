#!/bin/bash

CUR=${PWD}
INSTALL_DIR=${CUR}/install

echo "******************************************"
echo "${CUR}"
echo "${MLC_CUSPARSELT_TAR_FILE_PATH}"
echo "${MLC_CUSPARSELT_TAR_DIR}"
echo "${MLC_CUSPARSELT_UNTAR_PATH}"
echo "${CUDA_HOME}"
echo "${MLC_CUDA_PATH_INCLUDE}"
echo "${MLC_CUDA_PATH_LIB}"
echo "******************************************"

echo "Untaring file ..."
echo ""
tar -xf ${MLC_CUSPARSELT_TAR_FILE_PATH}
test $? -eq 0 || exit $?

echo "Copying include files ..."
echo ""
${MLC_SUDO} cp -P ${MLC_CUSPARSELT_TAR_DIR}/include/cusparseLt*.h ${MLC_CUDA_PATH_INCLUDE}
${MLC_SUDO} chmod a+r ${MLC_CUDA_PATH_INCLUDE}/cusparseLt*.h

echo "Copying lib files ..."
echo ""
${MLC_SUDO} cp -P ${MLC_CUSPARSELT_TAR_DIR}/lib/libcusparseLt* ${MLC_CUDA_PATH_LIB}
${MLC_SUDO} chmod a+r ${MLC_CUDA_PATH_LIB}/libcusparseLt*

echo "Adding file that CUSPARSELT is installed ..."
echo ""
if [ "${MLC_SUDO}" == "sudo" ]; then
  ${MLC_SUDO} sh -c "echo '${MLC_VERSION}' > ${CUDA_HOME}/mlc_installed_cusparselt.txt"
else
  echo "${MLC_VERSION}" > ${CUDA_HOME}/mlc_installed_cusparselt.txt
fi
