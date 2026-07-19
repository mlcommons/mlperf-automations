#!/bin/bash

CUR_DIR=$PWD

if [ "${MLC_TVM_PIP_INSTALL}" != "no" ]; then
  exit 0;
fi

echo "******************************************************"
echo "Path for TVM: ${CUR_DIR}"
echo ""

if [ ! -d "tvm" ]; then
  echo "git clone --recursive -b ${MLC_GIT_CHECKOUT} ${MLC_GIT_URL} tvm"
  git clone --recursive -b "${MLC_GIT_CHECKOUT}" ${MLC_GIT_URL} tvm
  test $? -eq 0 || exit 1
fi

cd tvm
if [ "${MLC_GIT_SHA}" != "" ]; then
  echo "git checkout ${MLC_GIT_SHA}"
  git checkout ${MLC_GIT_SHA}
  test $? -eq 0 || exit 1
fi


if [ ! -d "${CUR_DIR}/tvm/build" ]; then
    echo "******************************************************"
    echo "Configuring TVM ..."
    echo ""

    mkdir -p "${CUR_DIR}/tvm/build"

    cp cmake/config.cmake ${CUR_DIR}/tvm/build

    cd ${CUR_DIR}/tvm/build

    if [[ ${MLC_TVM_USE_LLVM} == "yes" ]]; then
        if [[ -z "${MLC_LLVM_INSTALLED_PATH}" ]]; then
            llvm_version=$(echo "${MLC_LLVM_CLANG_VERSION}" | cut -d. -f1)
            sed -i.bak "s|set(USE_LLVM OFF)|set(USE_LLVM llvm-config-$llvm_version)|" config.cmake
        else
            sed -i.bak "s|set(USE_LLVM OFF)|set(USE_LLVM ${MLC_LLVM_INSTALLED_PATH}/llvm-config)|" config.cmake
        fi
    fi

    if [[ ${MLC_TVM_USE_OPENMP} == "yes" ]]; then
        sed -i.bak 's/set(USE_OPENMP none)/set(USE_OPENMP gnu)/' config.cmake
    fi

    if [[ ${MLC_TVM_USE_CUDA} == "yes" ]]; then
        sed -i.bak 's/set(USE_CUDA OFF)/set(USE_OPENMP ON)/' config.cmake
        echo 'set(USE_CUDA ON)' >> config.cmake
    fi

    cmake ..
    test $? -eq 0 || exit 1
fi

MLC_MAKE_CORES=${MLC_MAKE_CORES:-${MLC_HOST_CPU_TOTAL_CORES}}
MLC_MAKE_CORES=${MLC_MAKE_CORES:-2}

echo "******************************************************"
echo "Building  TVM using ${MLC_MAKE_CORES} cores ..."
echo ""

cd ${CUR_DIR}/tvm/build

make -j${MLC_MAKE_CORES}
test $? -eq 0 || exit 1

INSTALL_DIR=$PWD

cd ../../

echo "TVM_HOME=$PWD/tvm" > tmp-run-env.out
echo "MLC_TVM_INSTALLED_PATH=$PWD/tvm" >> tmp-run-env.out

echo "******************************************************"
echo "TVM was built and installed to ${INSTALL_DIR} ..."
