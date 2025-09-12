#!/bin/bash

CUR_DIR=$PWD

INSTALL_DIR="${MLC_LLVM_INSTALLED_PATH}"
echo "INSTALL_DIR=${INSTALL_DIR}"

if [[ ${MLC_LLVM_CONDA_ENV} != "yes" ]]; then
    cmd="rm -rf ${INSTALL_DIR}"
    echo "$cmd"
    eval "$cmd"
else
    export PATH=${MLC_CONDA_BIN_PATH}:$PATH
fi

if [[ ${MLC_CLEAN_BUILD} == "yes" ]]; then
  rm -rf build
fi

mkdir -p build

# If install exist, then configure was done 
if [ ! -d "${INSTALL_DIR}" ] || [ ${MLC_LLVM_CONDA_ENV} == "yes" ]; then
    echo "******************************************************"

    cd build
    if [ "${?}" != "0" ]; then exit 1; fi

    echo "${MLC_LLVM_CMAKE_CMD}"
    eval "${MLC_LLVM_CMAKE_CMD}"
    ninja
    if [ "${?}" != "0" ]; then exit 1; fi
    ninja install
    if [ "${?}" != "0" ]; then exit 1; fi

fi

# Clean build directory (too large)
cd ${CUR_DIR}
rm -rf build

echo "******************************************************"
echo "LLVM is built and installed to ${INSTALL_DIR} ..."
