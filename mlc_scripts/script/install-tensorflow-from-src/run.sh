#!/bin/bash

CUR_DIR=${PWD:-tmp}
if [ ! -d "src" ]; then
  echo "Cloning Tensorflow from ${MLC_GIT_URL} with branch ${MLC_GIT_CHECKOUT} --depth ${MLC_GIT_DEPTH}..."
  git clone --recursive -b "${MLC_GIT_CHECKOUT}" ${MLC_GIT_URL} --depth ${MLC_GIT_DEPTH} src
fi
MLC_PYTHON_BIN=${MLC_PYTHON_BIN:-python3}

INSTALL_DIR="${CUR_DIR}"

echo "******************************************************"
cd src
#./configure
#if [ "${?}" != "0" ]; then exit 1; fi

if [ "${MLC_TFLITE}" == "on" ]; then
    cmd="${MLC_BAZEL_BIN_WITH_PATH} build -c opt --define tflite_with_xnnpack=true //tensorflow/lite:libtensorflowlite.so"
    echo $cmd
    eval $cmd
    if [ "${?}" != "0" ]; then exit 1; fi
    exit 0
fi
./configure
if [ "${?}" != "0" ]; then exit 1; fi
echo "******************************************************"
cmd="${MLC_BAZEL_BIN_WITH_PATH} build //tensorflow/tools/pip_package:build_pip_package"
echo $cmd
eval $cmd
if [ "${?}" != "0" ]; then exit 1; fi

echo "******************************************************"
./bazel-bin/tensorflow/tools/pip_package/build_pip_package /tmp/tensorflow_pkg
if [ "${?}" != "0" ]; then exit 1; fi


# Clean build directory (too large)
cd ${INSTALL_DIR}
if [ "${MLC_TENSORFLOW_CLEAN_BUILD}" != "no" ]; then
    rm -rf build
fi

echo "******************************************************"
echo "Tensorflow is built and installed to ${INSTALL_DIR} ..."
