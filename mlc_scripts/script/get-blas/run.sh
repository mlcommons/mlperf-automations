#!/bin/bash
CUR=$PWD
mkdir -p install
test $? -eq 0 || exit $?
INSTALL_DIR=$PWD/install
cd ${MLC_BLAS_SRC_PATH}
make -j${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES}
test $? -eq 0 || exit $?
make PREFIX=$INSTALL_DIR install
test $? -eq 0 || exit $?
