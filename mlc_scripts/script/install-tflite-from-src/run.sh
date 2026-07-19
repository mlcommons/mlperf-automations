#!/bin/bash

CUR_DIR=${PWD:-tmp}
if [ ! -d "src" ]; then
  echo "Cloning Tensorflow from ${MLC_GIT_URL} with branch ${MLC_GIT_CHECKOUT} --depth ${MLC_GIT_DEPTH}..."
  git clone --recursive -b "${MLC_GIT_CHECKOUT}" ${MLC_GIT_URL} --depth ${MLC_GIT_DEPTH} src
fi

INSTALL_DIR="${CUR_DIR}"
rm -rf ${INSTALL_DIR}/build

cd ${INSTALL_DIR}
mkdir -p build
mkdir -p install

echo "******************************************************"
cd build
cmake ../src/tensorflow/lite/c
if [ "${?}" != "0" ]; then exit 1; fi

echo "******************************************************"
cmake --build . -j${MLC_MAKE_CORES}
if [ "${?}" != "0" ]; then exit 1; fi


echo "******************************************************"
echo "Tflite is built to ${INSTALL_DIR}/build ..."
