#!/bin/bash

CUR_DIR=$PWD

echo "***********************************************************"
MLC_MAKE_CORES=${MLC_MAKE_CORES:-${MLC_HOST_CPU_TOTAL_CORES}}
MLC_MAKE_CORES=${MLC_MAKE_CORES:-2}
MLC_WGET_URL=https://github.com/gflags/gflags/archive/refs/tags/v${MLC_VERSION}.tar.gz
wget -nc ${MLC_WGET_URL}
test $? -eq 0 || exit 1
tar -xzf "v${MLC_VERSION}.tar.gz" && cd gflags-${MLC_VERSION}
test $? -eq 0 || exit 1
rm -rf build
mkdir build && cd build
cmake ..
make -j${MLC_MAKE_CORES}
test $? -eq 0 || exit 1
sudo make install
